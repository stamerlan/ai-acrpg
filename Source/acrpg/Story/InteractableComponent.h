#pragma once

#include "CoreMinimal.h"
#include "Components/SphereComponent.h"
#include "DlgSystem/DlgDialogueParticipant.h"
#include "StoryTypes.h"
#include "InteractableComponent.generated.h"

class UDlgDialogue;

/**
 *  Something she can talk to, pick up or use. The sphere is the range in
 *  which the prompt shows. BPC_Interactable implements the interaction,
 *  BPC_Interactor on the protagonist finds the closest one.
 *
 *  For Talk it is also the NPC's dialogue participant: dialogue nodes
 *  owned by ParticipantName show DisplayName as the speaker.
 */
UCLASS(Abstract, Blueprintable, ClassGroup = (Story),
	meta = (BlueprintSpawnableComponent))
class UInteractableComponent : public USphereComponent,
	public IDlgDialogueParticipant
{
	GENERATED_BODY()

public:

	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	EInteractType Type = EInteractType::Talk;

	/** Verb on the prompt, for example "Talk" or "Pick up" */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	FText Prompt;

	/** Talk: the dialogue */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	TObjectPtr<UDlgDialogue> Dialogue;

	/**
	 *  Talk: which way into the dialogue. The Story participant passes the
	 *  named condition "entry_<Entry>"; None takes the default start edge.
	 */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	FName Entry;

	/** Talk: the NPC's participant name in the dialogue */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	FName ParticipantName;

	/** Talk: the speaker name shown in the dialog window */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	FText DisplayName;

	/** The prompt shows only while all of them pass */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	TArray<FStoryCondition> Conditions;

	/** Run on every interaction, before the dialog starts */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Interaction")
	TArray<FStoryAction> Actions;

	UInteractableComponent();

	virtual FName GetParticipantName_Implementation() const override
	{
		return ParticipantName;
	}

	virtual FText GetParticipantDisplayName_Implementation(
		FName ActiveSpeaker) const override
	{
		return DisplayName;
	}
};
