#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "QuestDefinition.generated.h"

/** What the journal shows for one step of a quest */
USTRUCT(BlueprintType)
struct FQuestStepText
{
	GENERATED_BODY()

	/** Quest step from the story id table, for example office */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	FName Step;

	/** The journal line while the quest is at this step */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest",
		meta = (MultiLine = true))
	FText Text;

	/** The quest is finished at this step */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	bool bFinished = false;
};

/**
 *  What the journal knows about a quest. The story state only keeps the
 *  current step; this asset adds the title and a line per step. One asset
 *  per quest id, in /Game/Story/Quests (DA_Quest_<Name>).
 */
UCLASS(BlueprintType)
class UQuestDefinition : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:

	/** Story quest id, for example q_car_trouble */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	FName Id;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	FText Title;

	/** Main quests first, then by sort order */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	bool bMain = false;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	int32 SortOrder = 0;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Quest")
	TArray<FQuestStepText> Steps;

	/** Journal line and finished state of a step, false if it has none */
	UFUNCTION(BlueprintPure, Category = "Quest")
	bool FindStep(FName Step, FText& Text, bool& bFinished) const;

	/** Every quest definition, main quests first, then by sort order */
	UFUNCTION(BlueprintCallable, Category = "Quest")
	static TArray<UQuestDefinition*> GetAllQuests();
};
