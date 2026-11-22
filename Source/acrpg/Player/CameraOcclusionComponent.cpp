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

	Super::EndPlay(EndPlayReason);
}

void UCameraOcclusionComponent::FindOccluders(
	const FVector& CameraLocation,
	TSet<UPrimitiveComponent*>& OutOccluders) const
{
	const AActor* Owner = GetOwner();
	const FCollisionShape Sphere = FCollisionShape::MakeSphere(ProbeRadius);

	for (const FVector& Offset : ProbeOffsets)
	{
		const FVector Target = Owner->GetActorLocation() + Offset;
		const FVector Direction = (Target - CameraLocation).GetSafeNormal();
		const float TargetDistance = FVector::Dist(CameraLocation, Target);
		FCollisionQueryParams Params(SCENE_QUERY_STAT(CameraOcclusion));
		Params.AddIgnoredActor(Owner);

		// Single sweeps stop at the first blocker, so ignore each hit and
		// sweep again to find the occluders behind it
		for (int32 Index = 0; Index < MaxOccludersPerProbe; ++Index)
		{
			FHitResult Hit;
			if (!GetWorld()->SweepSingleByChannel(Hit, CameraLocation,
				Target, FQuat::Identity, TraceChannel, Sphere, Params))
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

			// The sphere also touches a wall the owner stands against with
			// the camera in front of her, so cut only surfaces in front of
			// the probe point along the camera ray
			const bool bInFront = FVector::DotProduct(
				Hit.ImpactPoint - CameraLocation, Direction) < TargetDistance;
			if (bInFront && !Cast<APawn>(HitActor) &&
				!(HitActor && HitActor->ActorHasTag(NoOcclusionCutoutTag)))
			{
				OutOccluders.Add(Component);
			}
		}
	}
}
