#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "CombatTypes.h"
#include "SaveSubsystem.generated.h"

class UAcrpgSaveGame;

/**
 *  The save on disk. Every checkpoint in a gameplay map (SavedMapPrefixes
 *  in Project Settings > Game > Story) writes its snapshot to the slot
 *  "Checkpoint" (UAcrpgSaveGame); the save it replaces moves to
 *  "Checkpoint_Prev". Continue hands the saved snapshot to the checkpoint
 *  subsystem and reloads it the way a death does, so both end in the same
 *  state.
 *
 *  A save that can't be read, has another SaveVersion or points to a
 *  missing map is ignored with a log line and the backup is tried. With
 *  neither usable HasSave is false and the next checkpoint overwrites it.
 *
 *  Play started straight in a map (in the editor, without NewGame or
 *  Continue) doesn't write its LevelStart snapshot over a usable save, so
 *  the last session's save stays until she reaches a checkpoint.
 *
 *  Console: Save.Info, Save.Continue, Save.Delete.
 */
UCLASS()
class USaveSubsystem : public UGameInstanceSubsystem
{
	GENERATED_BODY()

	/** The save Continue loads, null when there is none */
	UPROPERTY(Transient)
	TObjectPtr<UAcrpgSaveGame> Current;

	/** NewGame or Continue ran or a checkpoint was written this session */
	bool bSessionStarted = false;

public:

	/** Reads the slot, the backup when the slot can't be used */
	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** True when there is a save that Continue can load */
	UFUNCTION(BlueprintPure, Category = "Save")
	bool HasSave() const { return Current != nullptr; }

	/** Restores the save and opens its map at its checkpoint */
	UFUNCTION(BlueprintCallable, Category = "Save",
		meta = (WorldContext = "WorldContext"))
	void Continue(const UObject* WorldContext);

	/**
	 *  Deletes the save, clears the story state and the checkpoint and
	 *  opens NewGameMap from Project Settings > Game > Story.
	 */
	UFUNCTION(BlueprintCallable, Category = "Save",
		meta = (WorldContext = "WorldContext"))
	void NewGame(const UObject* WorldContext);

	/** Deletes the save and its backup, the game in memory goes on */
	UFUNCTION(BlueprintCallable, Category = "Save")
	void DeleteSave();

	/**
	 *  Writes a checkpoint snapshot to the slot. The checkpoint subsystem
	 *  calls it; bArrival is true for a LevelStart snapshot.
	 */
	void WriteSave(const FCheckpointSnapshot& Snapshot, bool bArrival);

	/** The save Continue loads and the state of both files, for Save.Info */
	TArray<FString> Describe() const;
};
