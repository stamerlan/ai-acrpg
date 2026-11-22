#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CameraOcclusionComponent.generated.h"

class UPrimitiveComponent;

/**
 *  Finds primitives between the owner's camera and the owner and drives
 *  their custom primitive data, so materials using MF_OcclusionCutout cut
 *  a hole around the owner, in pixels closer to the camera than the owner:
 *   - FadeDataIndex: cutout amount, 0 (none) to 1 (full)
 *   - FadeDataIndex + 1, + 2: owner position in viewport UV
 *   - FadeDataIndex + 3: owner view depth
 *  Actors tagged NoOcclusionCutout are never cut.
 */
UCLASS(ClassGroup = (Camera), meta = (BlueprintSpawnableComponent))
class UCameraOcclusionComponent : public UActorComponent
{
	GENERATED_BODY()

protected:

	/** Channel used to find occluders */
	UPROPERTY(EditAnywhere, Category = "Occlusion")
	TEnumAsByte<ECollisionChannel> TraceChannel = ECC_Camera;

	/** Radius of the sphere swept from the camera to each probe point */
	UPROPERTY(EditAnywhere, Category = "Occlusion",
		meta = (ClampMin = 0, Units = "cm"))
	float ProbeRadius = 30.f;

	/** Points relative to the owner location that must stay visible */
	UPROPERTY(EditAnywhere, Category = "Occlusion")
	TArray<FVector> ProbeOffsets = {FVector(0.f, 0.f, 0.f),
		FVector(0.f, 0.f, 70.f)};

	/** Occluders found per probe, stacked walls beyond are not cut */
	UPROPERTY(EditAnywhere, Category = "Occlusion", meta = (ClampMin = 1))
	int32 MaxOccludersPerProbe = 8;

	/** Time for the cutout to fully open or close */
	UPROPERTY(EditAnywhere, Category = "Occlusion",
		meta = (ClampMin = 0.01, Units = "s"))
	float FadeTime = 0.2f;

	/** First of the four custom primitive data floats it writes */
	UPROPERTY(EditAnywhere, Category = "Occlusion", meta = (ClampMin = 0))
	int32 FadeDataIndex = 0;

	/** Occluders with their current cutout amount */
	TMap<TWeakObjectPtr<UPrimitiveComponent>, float> Occluders;

public:

	UCameraOcclusionComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

protected:

	/** Adds every primitive between the camera and the probe points */
	void FindOccluders(const FVector& CameraLocation,
		TSet<UPrimitiveComponent*>& OutOccluders) const;
};
