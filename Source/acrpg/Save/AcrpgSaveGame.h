#pragma once

#include "CoreMinimal.h"
#include "GameFramework/SaveGame.h"
#include "CombatTypes.h"
#include "AcrpgSaveGame.generated.h"

/**
 *  The save on disk: the last checkpoint snapshot, written by
 *  USaveSubsystem. A save of another SaveVersion is ignored.
 */
UCLASS()
class UAcrpgSaveGame : public USaveGame
{
	GENERATED_BODY()

public:

	/**
	 *  Format of the saves this build writes and reads. Bump it when a
	 *  change to FCheckpointSnapshot (or to a struct in it) would load an
	 *  old save wrong: renamed or retyped fields, ids with a new meaning.
	 */
	static constexpr int32 CurrentVersion = 1;

	/** Format the save was written with, 0 when unknown */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, SaveGame, Category = "Save")
	int32 SaveVersion = 0;

	/** Local time the save was written */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, SaveGame, Category = "Save")
	FDateTime SavedAt;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, SaveGame, Category = "Save")
	FCheckpointSnapshot Checkpoint;
};
