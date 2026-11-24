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
 *  Roofs right above the owner are hidden (see RoofCheckHeight).
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

	/**
	 *  Height above the owner searched for roofs. Every part of a roof's
	 *  actor over it that is at least RoofMinHeight above her (the roof,
	 *  signs on it) is hidden, so the whole room or stall she is in shows.
	 *  Hidden parts keep their shadow. 0 turns the check off.
	 */
	UPROPERTY(EditAnywhere, Category = "Occlusion",
		meta = (ClampMin = 0, Units = "cm"))
	float RoofCheckHeight = 1000.f;

	/** Lowest a roof part may reach above the owner, walls reach lower */
	UPROPERTY(EditAnywhere, Category = "Occlusion",
		meta = (ClampMin = 0, Units = "cm"))
	float RoofMinHeight = 100.f;

	/** Time for the cutout to fully open or close */
	UPROPERTY(EditAnywhere, Category = "Occlusion",
		meta = (ClampMin = 0.01, Units = "s"))
	float FadeTime = 0.2f;

	/** First of the four custom primitive data floats it writes */
	UPROPERTY(EditAnywhere, Category = "Occlusion", meta = (ClampMin = 0))
	int32 FadeDataIndex = 0;

	/** Occluders with their current cutout amount */
	TMap<TWeakObjectPtr<UPrimitiveComponent>, float> Occluders;

	/** Roof parts hidden now, with their own cast hidden shadow flag */
	TMap<TWeakObjectPtr<UPrimitiveComponent>, bool> HiddenRoofs;

public:

	UCameraOcclusionComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

protected:

	/** Adds every primitive between the camera and the probe points */
	void FindOccluders(const FVector& CameraLocation,
		TSet<UPrimitiveComponent*>& OutOccluders) const;

	/**
	 *  Hides the roof parts above the owner and shows the ones she left.
	 *  Primitives above her that are not roofs (tree tops) are added to
	 *  OutOccluders to get the cutout.
	 */
	void UpdateRoofs(TSet<UPrimitiveComponent*>& OutOccluders);

	/** Adds every primitive the shape touches from Start to Target */
	void SweepOccluders(const FVector& Start, const FVector& Target,
		const FCollisionShape& Shape,
		TSet<UPrimitiveComponent*>& OutOccluders) const;
};
