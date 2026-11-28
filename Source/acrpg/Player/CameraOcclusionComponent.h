#pragma once

#include "CoreMinimal.h"
#include "Components/ActorComponent.h"
#include "CameraOcclusionComponent.generated.h"

class UPrimitiveComponent;

/**
 *  Hides the roofs between the owner's camera and the owner, and the ones
 *  right above her, so the room or stall she is in shows. Walls and other
 *  things that hide her stay whole: M_PP_Silhouette draws her through
 *  them (her custom depth, see AChickenCharacter). An actor tagged
 *  HideWhole (a walk-in shop's roof with the wall over its door) hides
 *  all its parts when any of them is hit.
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

	/** Occluders found per probe, stacked walls beyond are not checked */
	UPROPERTY(EditAnywhere, Category = "Occlusion", meta = (ClampMin = 1))
	int32 MaxOccludersPerProbe = 8;

	/**
	 *  Height above the owner searched for roofs, 0 turns this check off.
	 *  For a primitive found here or between the camera and her, every
	 *  part of its actor over it that is at least RoofMinHeight above her
	 *  (a roof, a tarp, signs on it) is hidden, so the whole room or stall
	 *  shows. Hidden parts keep their shadow.
	 */
	UPROPERTY(EditAnywhere, Category = "Occlusion",
		meta = (ClampMin = 0, Units = "cm"))
	float RoofCheckHeight = 1000.f;

	/** Lowest a roof part may reach above the owner, walls reach lower */
	UPROPERTY(EditAnywhere, Category = "Occlusion",
		meta = (ClampMin = 0, Units = "cm"))
	float RoofMinHeight = 100.f;

	/** Roof parts hidden now, with their own cast hidden shadow flag */
	TMap<TWeakObjectPtr<UPrimitiveComponent>, bool> HiddenRoofs;

public:

	UCameraOcclusionComponent();

	virtual void TickComponent(float DeltaTime, ELevelTick TickType,
		FActorComponentTickFunction* ThisTickFunction) override;

	virtual void EndPlay(const EEndPlayReason::Type EndPlayReason) override;

protected:

	/**
	 *  Adds every primitive between the camera and the probe points, and
	 *  every one right above the owner
	 */
	void FindOccluders(const FVector& CameraLocation,
		TSet<UPrimitiveComponent*>& OutOccluders) const;

	/**
	 *  Hides the roof parts of the hit actors and shows the ones that no
	 *  longer cover the owner
	 */
	void UpdateRoofs(const TSet<UPrimitiveComponent*>& Hits);

	/** Adds every primitive the shape touches from Start to Target */
	void SweepOccluders(const FVector& Start, const FVector& Target,
		const FCollisionShape& Shape,
		TSet<UPrimitiveComponent*>& OutOccluders) const;
};
