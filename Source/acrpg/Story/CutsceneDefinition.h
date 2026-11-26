#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "CutsceneDefinition.generated.h"

class ULevelSequence;
class USoundBase;

/** One subtitle line of a cutscene or a radio broadcast */
USTRUCT(BlueprintType)
struct FStoryLine
{
	GENERATED_BODY()

	/** Seconds from the start of the cutscene */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cutscene")
	float Time = 0.f;

	/** How long the line stays on screen, in seconds */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cutscene")
	float Duration = 3.f;

	/** Shown before the line, for example RADIO. Empty: no speaker. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cutscene")
	FText Speaker;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cutscene",
		meta = (MultiLine = true))
	FText Text;
};

/**
 *  A cutscene (a level sequence) or a radio broadcast (a sound) with its
 *  subtitles. BP_StoryDirector plays them. One asset per cutscene, in
 *  /Game/Story/<Stop>/Cutscenes (DA_Cutscene_<Name>).
 */
UCLASS(BlueprintType)
class UCutsceneDefinition : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:

	/** The cutscene; none for a radio broadcast in the world */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cutscene")
	TObjectPtr<ULevelSequence> Sequence;

	/** Played with the subtitles when there is no sequence */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cutscene")
	TObjectPtr<USoundBase> Sound;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cutscene")
	TArray<FStoryLine> Lines;

	/** Length of a broadcast without a sequence, for its subtitles */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Cutscene")
	float Length = 0.f;
};
