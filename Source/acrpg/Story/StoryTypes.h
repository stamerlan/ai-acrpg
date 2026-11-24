#pragma once

#include "CoreMinimal.h"
#include "Engine/DataTable.h"
#include "StoryTypes.generated.h"

/** Kind of a story state id */
UENUM(BlueprintType)
enum class EStoryIdKind : uint8
{
	/** Has one current step, None when not started */
	Quest,
	/** Bool (value "true" or None) or one of a list of values */
	Flag,
	/** Checklist stamp, set or not */
	Stamp,
	/** Inventory item with a count */
	Item
};

/** A test against the story state */
UENUM(BlueprintType)
enum class EStoryConditionType : uint8
{
	/** Flag Id has Value (None: the flag is not set) */
	FlagIs,
	FlagIsNot,
	/** Quest Id is at step Value (None: not started) */
	QuestIs,
	QuestIsNot,
	/** At least Count of item Id */
	HasItem,
	/** Less than Count of item Id */
	LacksItem
};

/** A change to the story state */
UENUM(BlueprintType)
enum class EStoryActionType : uint8
{
	/** Sets flag Id to Value, None clears it */
	SetFlag,
	/** Sets quest Id to step Value */
	SetQuest,
	/** Adds stamp Id */
	AddStamp,
	/** Gives Count of item Id */
	GiveItem,
	/** Takes Count of item Id */
	TakeItem,
	/** Broadcasts story event Id, for level scripts */
	Event
};

/** What happens when she interacts with an object */
UENUM(BlueprintType)
enum class EInteractType : uint8
{
	/** Starts a dialog */
	Talk,
	/** Runs the actions and removes the object */
	PickUp,
	/** Runs the actions, the object stays */
	Use,
	/** She picks the object up to carry and throw it (BPC_Carry) */
	Carry
};

USTRUCT(BlueprintType)
struct FStoryCondition
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	EStoryConditionType Type = EStoryConditionType::FlagIs;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	FName Id;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	FName Value;

	/** Item count for HasItem and LacksItem */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	int32 Count = 1;
};

USTRUCT(BlueprintType)
struct FStoryAction
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	EStoryActionType Type = EStoryActionType::SetFlag;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	FName Id;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	FName Value;

	/** Item count for GiveItem and TakeItem */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	int32 Count = 1;
};

/** Definition of a story id, a row of a story id table */
USTRUCT(BlueprintType)
struct FStoryIdRow : public FTableRowBase
{
	GENERATED_BODY()

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	EStoryIdKind Kind = EStoryIdKind::Flag;

	/** Quest steps in order, or flag values. A flag without is a bool. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	TArray<FName> Values;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Story")
	FString Description;
};

/** Everything the story remembers. Saves store this struct as is. */
USTRUCT(BlueprintType)
struct FStoryState
{
	GENERATED_BODY()

	/** Quest id to its current step */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Story")
	TMap<FName, FName> Quests;

	/** Flag id to its value, bool flags hold "true" */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Story")
	TMap<FName, FName> Flags;

	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Story")
	TSet<FName> Stamps;

	/** Item id to its count, never zero */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, SaveGame, Category = "Story")
	TMap<FName, int32> Items;
};
