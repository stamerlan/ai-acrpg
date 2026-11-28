#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "CombatTypes.h"
#include "CheckpointSubsystem.generated.h"

/**
 *  Checkpoints: the last one is a snapshot of the game state in memory,
 *  and USaveSubsystem writes each one to disk. A reload restores the story
 *  state and the defeated actors, reopens the map and puts her back at the
 *  checkpoint with the health she had there.
 *
 *  The player calls OnPlayerBeginPlay. Arriving in a map without a
 *  checkpoint there saves a LevelStart snapshot, so a reload always has
 *  somewhere to go.
 *
 *  Console: Checkpoint.Reload, Checkpoint.Info.
 */
UCLASS()
class UCheckpointSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

	UPROPERTY(Transient)
	FCheckpointSnapshot Last;

	bool bHasCheckpoint = false;

	/** Set by a reload, consumed by OnPlayerBeginPlay in the new map */
	bool bPendingRestore = false;

	/** Actors defeated in the current map since it was opened */
	TSet<FName> Defeated;

	/** Map the defeated set belongs to */
	FString DefeatedMap;

public:

	/** Saves the current state as the last checkpoint */
	UFUNCTION(BlueprintCallable, Category = "Checkpoint",
		meta = (WorldContext = "WorldContext"))
	void SaveCheckpoint(const UObject* WorldContext, FName CheckpointId,
		const FTransform& PlayerTransform, float Health, FName Phase);

	/** Restores the last checkpoint and reopens its map */
	UFUNCTION(BlueprintCallable, Category = "Checkpoint",
		meta = (WorldContext = "WorldContext"))
	void ReloadLastCheckpoint(const UObject* WorldContext);

	/**
	 *  Call when the player begins play. After a reload it moves her to
	 *  the checkpoint and returns true with the health to restore. In a
	 *  map without a checkpoint it saves the LevelStart snapshot.
	 */
	UFUNCTION(BlueprintCallable, Category = "Checkpoint")
	bool OnPlayerBeginPlay(AActor* Player, float Health,
		float& RestoredHealth);

	/** Remembers that a level actor was defeated */
	UFUNCTION(BlueprintCallable, Category = "Checkpoint")
	void MarkDefeated(const AActor* Actor);

	/** True when a level actor was defeated before (it stays defeated) */
	UFUNCTION(BlueprintPure, Category = "Checkpoint")
	bool IsDefeated(const AActor* Actor) const;

	UFUNCTION(BlueprintPure, Category = "Checkpoint")
	bool HasCheckpoint() const { return bHasCheckpoint; }

	UFUNCTION(BlueprintPure, Category = "Checkpoint")
	const FCheckpointSnapshot& GetLastCheckpoint() const { return Last; }

	/** Replaces the last checkpoint, for loading saves */
	UFUNCTION(BlueprintCallable, Category = "Checkpoint")
	void SetLastCheckpoint(const FCheckpointSnapshot& Snapshot);

	/** Forgets the last checkpoint and the defeated actors, for New game */
	UFUNCTION(BlueprintCallable, Category = "Checkpoint")
	void ResetCheckpoints();

	/** One line about a snapshot, for the console */
	static FString Describe(const FCheckpointSnapshot& Snapshot);

private:

	/** Long package name of the world's map without the PIE prefix */
	static FString GetMapName(const UWorld* World);

	/** Clears the defeated set when the world is another map */
	void UpdateDefeatedMap(const UWorld* World);
};
