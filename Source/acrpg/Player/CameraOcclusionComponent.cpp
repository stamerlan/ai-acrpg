#include "CameraOcclusionComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

// Buildings, her car, poles: never hidden, she shows as a silhouette
static const FName NoOcclusionCutoutTag(TEXT("NoOcclusionCutout"));

// A walk-in shop roof with the wall over its door: hidden all at once
static const FName HideWholeTag(TEXT("HideWhole"));

UCameraOcclusionComponent::UCameraOcclusionComponent()
{
	PrimaryComponentTick.bCanEverTick = true;
	PrimaryComponentTick.TickGroup = TG_PostUpdateWork;
}

void UCameraOcclusionComponent::TickComponent(float DeltaTime,
	ELevelTick TickType, FActorComponentTickFunction* ThisTickFunction)
{
	Super::TickComponent(DeltaTime, TickType, ThisTickFunction);

	const APawn* Pawn = Cast<APawn>(GetOwner());
	const APlayerController* PC =
		Pawn ? Cast<APlayerController>(Pawn->GetController()) : nullptr;
	if (!PC || !PC->PlayerCameraManager)
	{
		return;
	}

	TSet<UPrimitiveComponent*> Hits;
	FindOccluders(PC->PlayerCameraManager->GetCameraLocation(), Hits);
	UpdateRoofs(Hits);
}

void UCameraOcclusionComponent::EndPlay(
	const EEndPlayReason::Type EndPlayReason)
{
	for (const auto& Pair : HiddenRoofs)
	{
		if (UPrimitiveComponent* Component = Pair.Key.Get())
		{
			Component->SetHiddenInGame(false);
			Component->SetCastHiddenShadow(Pair.Value);
		}
	}
	HiddenRoofs.Empty();

	Super::EndPlay(EndPlayReason);
}

void UCameraOcclusionComponent::FindOccluders(
	const FVector& CameraLocation,
	TSet<UPrimitiveComponent*>& OutOccluders) const
{
	const FVector OwnerLocation = GetOwner()->GetActorLocation();
	const FCollisionShape Sphere = FCollisionShape::MakeSphere(ProbeRadius);
	for (const FVector& Offset : ProbeOffsets)
	{
		SweepOccluders(CameraLocation, OwnerLocation + Offset, Sphere,
			OutOccluders);
	}

	// A steep camera ray passes under the edge of the roof she stands
	// under and only cuts a hole in the wall, so look straight up too
	if (RoofCheckHeight > 0.f)
	{
		SweepOccluders(OwnerLocation,
			OwnerLocation + FVector(0.f, 0.f, RoofCheckHeight),
			FCollisionShape::MakeSphere(0.f), OutOccluders);
	}
}

void UCameraOcclusionComponent::UpdateRoofs(
	const TSet<UPrimitiveComponent*>& Hits)
{
	// A roof is every part of a hit actor over the hit primitive that
	// stays above her: an art tarp, a graybox roof, the signs on a stall's
	// hidden graybox awning. Walls and posts reach the ground and stay.
	TSet<UPrimitiveComponent*> Roofs;
	const float MinZ = GetOwner()->GetActorLocation().Z + RoofMinHeight;
	for (UPrimitiveComponent* Hit : Hits)
	{
		if (!Hit->GetOwner())
		{
			continue;
		}
		const FBox HitBox = Hit->Bounds.GetBox();
		const FBox2D HitArea(FVector2D(HitBox.Min), FVector2D(HitBox.Max));
		const bool bWhole = Hit->GetOwner()->ActorHasTag(HideWholeTag);
		TInlineComponentArray<UPrimitiveComponent*> Parts(Hit->GetOwner());
		for (UPrimitiveComponent* Part : Parts)
		{
			const FBox Box = Part->Bounds.GetBox();
			const bool bShown = HiddenRoofs.Contains(Part) ||
				(Part->IsVisible() && !Part->bHiddenInGame);
			if (bShown && (bWhole || (Box.Min.Z >= MinZ && HitArea.Intersect(
				FBox2D(FVector2D(Box.Min), FVector2D(Box.Max))))))
			{
				Roofs.Add(Part);
			}
		}
	}

	for (auto It = HiddenRoofs.CreateIterator(); It; ++It)
	{
		UPrimitiveComponent* Component = It.Key().Get();
		if (Component && !Roofs.Contains(Component))
		{
			Component->SetHiddenInGame(false);
			Component->SetCastHiddenShadow(It.Value());
		}
		if (!Component || !Roofs.Contains(Component))
		{
			It.RemoveCurrent();
		}
	}
	for (UPrimitiveComponent* Component : Roofs)
	{
		if (!HiddenRoofs.Contains(Component))
		{
			HiddenRoofs.Add(Component, Component->bCastHiddenShadow);
			Component->SetCastHiddenShadow(true);
			Component->SetHiddenInGame(true);
		}
	}
}

void UCameraOcclusionComponent::SweepOccluders(const FVector& Start,
	const FVector& Target, const FCollisionShape& Shape,
	TSet<UPrimitiveComponent*>& OutOccluders) const
{
	const FVector Direction = (Target - Start).GetSafeNormal();
	const float TargetDistance = FVector::Dist(Start, Target);
	FCollisionQueryParams Params(SCENE_QUERY_STAT(CameraOcclusion));
	Params.AddIgnoredActor(GetOwner());

	// Single sweeps stop at the first blocker, so ignore each hit and
	// sweep again to find the occluders behind it
	for (int32 Index = 0; Index < MaxOccludersPerProbe; ++Index)
	{
		FHitResult Hit;
		if (!GetWorld()->SweepSingleByChannel(Hit, Start, Target,
			FQuat::Identity, TraceChannel, Shape, Params))
		{
			break;
		}

		UPrimitiveComponent* Component = Hit.GetComponent();
		const AActor* HitActor = Hit.GetActor();
		if (!Component)
		{
			break;
		}
		Params.AddIgnoredComponent(Component);

		// The sphere also touches a wall the owner stands against with the
		// camera in front of her, so take only surfaces in front of the
		// probe point along the ray
		const bool bInFront = FVector::DotProduct(
			Hit.ImpactPoint - Start, Direction) < TargetDistance;
		if (bInFront && !Cast<APawn>(HitActor) &&
			!(HitActor && HitActor->ActorHasTag(NoOcclusionCutoutTag)))
		{
			OutOccluders.Add(Component);
		}
	}
}
