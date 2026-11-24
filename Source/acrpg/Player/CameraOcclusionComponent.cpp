#include "CameraOcclusionComponent.h"
#include "Camera/PlayerCameraManager.h"
#include "Components/PrimitiveComponent.h"
#include "Engine/World.h"
#include "GameFramework/Pawn.h"
#include "GameFramework/PlayerController.h"

static const FName NoOcclusionCutoutTag(TEXT("NoOcclusionCutout"));

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

	const FVector CameraLocation =
		PC->PlayerCameraManager->GetCameraLocation();
	TSet<UPrimitiveComponent*> Current;
	FindOccluders(CameraLocation, Current);
	UpdateRoofs(Current);
	for (UPrimitiveComponent* Component : Current)
	{
		Occluders.FindOrAdd(Component, 0.f);
	}

	FVector2D Screen(0.5f, 0.5f);
	int32 ViewX = 0;
	int32 ViewY = 0;
	PC->GetViewportSize(ViewX, ViewY);
	if (PC->ProjectWorldLocationToScreen(Pawn->GetActorLocation(), Screen,
		true) && ViewX > 0 && ViewY > 0)
	{
		Screen /= FVector2D(ViewX, ViewY);
	}

	// View depth of the owner, the material cuts only pixels closer than it
	const float Depth = FVector::DotProduct(
		Pawn->GetActorLocation() - CameraLocation,
		PC->PlayerCameraManager->GetCameraRotation().Vector());

	const float Rate = 1.f / FadeTime;
	for (auto It = Occluders.CreateIterator(); It; ++It)
	{
		UPrimitiveComponent* Component = It.Key().Get();
		if (!Component)
		{
			It.RemoveCurrent();
			continue;
		}

		const bool bOccluding = Current.Contains(Component);
		It.Value() = FMath::FInterpConstantTo(It.Value(),
			bOccluding ? 1.f : 0.f, DeltaTime, Rate);
		Component->SetCustomPrimitiveDataFloat(FadeDataIndex, It.Value());
		Component->SetCustomPrimitiveDataFloat(FadeDataIndex + 1,
			Screen.X);
		Component->SetCustomPrimitiveDataFloat(FadeDataIndex + 2,
			Screen.Y);
		Component->SetCustomPrimitiveDataFloat(FadeDataIndex + 3, Depth);
		if (!bOccluding && It.Value() <= 0.f)
		{
			It.RemoveCurrent();
		}
	}
}

void UCameraOcclusionComponent::EndPlay(
	const EEndPlayReason::Type EndPlayReason)
{
	for (const auto& Pair : Occluders)
	{
		if (UPrimitiveComponent* Component = Pair.Key.Get())
		{
			Component->SetCustomPrimitiveDataFloat(FadeDataIndex, 0.f);
		}
	}
	Occluders.Empty();

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
}

void UCameraOcclusionComponent::UpdateRoofs(
	TSet<UPrimitiveComponent*>& OutOccluders)
{
	// A steep camera ray passes under the edge of the roof she stands
	// under and only cuts a hole in the wall, so look straight up
	const FVector OwnerLocation = GetOwner()->GetActorLocation();
	TSet<UPrimitiveComponent*> Above;
	if (RoofCheckHeight > 0.f)
	{
		SweepOccluders(OwnerLocation,
			OwnerLocation + FVector(0.f, 0.f, RoofCheckHeight),
			FCollisionShape::MakeSphere(0.f), Above);
	}

	// A roof is every part of the hit actor over the hit primitive that
	// stays above her: an art tarp, a graybox roof, the signs on a stall's
	// hidden graybox awning. Walls and posts reach the ground and stay.
	TSet<UPrimitiveComponent*> Roofs;
	const float MinZ = OwnerLocation.Z + RoofMinHeight;
	for (UPrimitiveComponent* Hit : Above)
	{
		if (!Hit->GetOwner())
		{
			continue;
		}
		const FBox HitBox = Hit->Bounds.GetBox();
		const FBox2D HitArea(FVector2D(HitBox.Min), FVector2D(HitBox.Max));
		TInlineComponentArray<UPrimitiveComponent*> Parts(Hit->GetOwner());
		for (UPrimitiveComponent* Part : Parts)
		{
			const FBox Box = Part->Bounds.GetBox();
			const bool bShown = HiddenRoofs.Contains(Part) ||
				(Part->IsVisible() && !Part->bHiddenInGame);
			if (bShown && Box.Min.Z >= MinZ && HitArea.Intersect(
				FBox2D(FVector2D(Box.Min), FVector2D(Box.Max))))
			{
				Roofs.Add(Part);
			}
		}
		if (!Roofs.Contains(Hit))
		{
			OutOccluders.Add(Hit);
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
		// camera in front of her, so cut only surfaces in front of the
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
