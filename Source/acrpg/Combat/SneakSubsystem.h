#pragma once

#include "CoreMinimal.h"
#include "Subsystems/WorldSubsystem.h"
#include "SneakSubsystem.generated.h"

class USpotLightComponent;

/**
 *  Sneaking rules shared by the enemies (GDD: Lights and sneaking).
 *
 *  Light: at night (while an actor tagged Darkness exists, the night
 *  post process volume) she is lit inside a lit zone or a light cone and
 *  in the dark everywhere else. By day everything counts as lit.
 *  - Lit zones are actors tagged LitZone (the graybox Lit markers); the
 *    horizontal extent of their disc mesh is the zone radius.
 *  - Light cones are spot lights tagged SightLight (on the component or
 *    on its actor) that are visible and switched on: the point must be
 *    within the attenuation radius and the outer cone angle, with nothing
 *    blocking the Visibility channel in between.
 *
 *  Noise: ReportNoise calls HearNoise(Location, Tag) on every actor
 *  within the radius that has such a function (BP_EnemyBase).
 *
 *  Console: Sneak.Info prints the lit zones, light cones and darkness.
 */
UCLASS()
class USneakSubsystem : public UWorldSubsystem
{
	GENERATED_BODY()

	/** Frame the cached lists below belong to */
	mutable uint64 CachedFrame = MAX_uint64;

	mutable bool bCachedDark = false;

	mutable TArray<TWeakObjectPtr<AActor>> CachedZones;

	mutable TArray<TWeakObjectPtr<USpotLightComponent>> CachedLights;

	void Refresh() const;

public:

	/** True while dark rules apply (an actor tagged Darkness exists) */
	UFUNCTION(BlueprintPure, Category = "Sneak")
	bool IsDark() const;

	/**
	 *  True when the point is lit: no darkness, inside a lit zone or
	 *  inside a light cone. Ignore is left out of the cone traces (pass
	 *  the actor standing at the point).
	 */
	UFUNCTION(BlueprintPure, Category = "Sneak")
	bool IsLit(FVector Location, AActor* Ignore) const;

	/** True when the point is inside this spot light's lit cone */
	UFUNCTION(BlueprintPure, Category = "Sneak")
	bool IsInLightCone(const USpotLightComponent* Light, FVector Location,
		AActor* Ignore) const;

	/**
	 *  A noise at Location: every actor within Radius that has a
	 *  HearNoise(Location, Tag) function gets it called.
	 */
	UFUNCTION(BlueprintCallable, Category = "Sneak")
	void ReportNoise(FVector Location, float Radius, FName Tag);

	/** Lit zones, light cones and darkness, for the console */
	FString Describe() const;
};
