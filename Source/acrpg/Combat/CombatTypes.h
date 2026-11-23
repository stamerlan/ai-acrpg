#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "StoryTypes.h"
#include "CombatTypes.generated.h"

class UTexture2D;

/**
 *  A death screen, a row of a death screen table. The row name is the
 *  "killed by" tag of the damage source. The row "Generic" holds the lines
 *  mixed into every killer's pool and is used for unknown killers.
 */
USTRUCT(BlueprintType)
struct FDeathScreenRow : public FTableRowBase
{
	GENERATED_BODY()

	/** What she became, shown under the picture */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Death")
	FText Dish;

	/** Full screen food picture, the plate color shows without one */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Death")
	TSoftObjectPtr<UTexture2D> Picture;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Death")
	FLinearColor PlateColor = FLinearColor(0.3f, 0.15f, 0.05f);

	/** Pun lines, one is picked at random */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Death")
	TArray<FText> Lines;
};

/** The game state saved by a checkpoint, kept in memory until a reload */
USTRUCT(BlueprintType)
struct FCheckpointSnapshot
{
	GENERATED_BODY()

	/** Checkpoint actor id, LevelStart for the arrival snapshot */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Save")
	FName CheckpointId;

	/** Long package name of the map, without the PIE prefix */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Save")
	FString Map;

	/** Level phase when a map holds more than one (stop 0: Day, Night) */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Save")
	FName Phase;

	/** Where she starts after a reload */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Save")
	FTransform PlayerTransform;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Save")
	float Health = 0.f;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Save")
	FStoryState Story;

	/** Names of the level actors defeated before the checkpoint */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Save")
	TSet<FName> Defeated;
};
