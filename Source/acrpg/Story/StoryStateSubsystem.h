#pragma once

#include "CoreMinimal.h"
#include "Subsystems/GameInstanceSubsystem.h"
#include "DlgSystem/DlgDialogueParticipant.h"
#include "StoryTypes.h"
#include "StoryStateSubsystem.generated.h"

DECLARE_DYNAMIC_MULTICAST_DELEGATE_ThreeParams(FStoryChangedSignature,
	EStoryIdKind, Kind, FName, Id, FName, Value);

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FStoryEventSignature,
	FName, Event);

/**
 *  Quests, flags, stamps and items: what the story remembers. Dialogs and
 *  level scripts read and write it, saves store GetState().
 *
 *  Ids are defined in the tables from the Story project settings. Using
 *  an id or a value that is not defined logs a warning.
 *
 *  It is also the "Story" participant of every dialogue: name values are
 *  quest steps and flags, bool values are bool flags and stamps, int
 *  values are item counts, events are story events. The named condition
 *  "entry_<name>" passes while the dialogue was started with that entry.
 *
 *  Console: Story.List, Story.Set <id> [value], Story.Event <name>,
 *  Story.Reset.
 */
UCLASS()
class UStoryStateSubsystem : public UGameInstanceSubsystem,
	public IDlgDialogueParticipant
{
	GENERATED_BODY()

	UPROPERTY(Transient)
	FStoryState State;

	/** All defined ids, loaded from the id tables */
	TMap<FName, FStoryIdRow> Definitions;

	/** Entry of the dialogue being started, see SetDialogueEntry */
	FName DialogueEntry;

public:

	/**
	 *  Any quest, flag, stamp or item changed. Value is the new one. Id
	 *  None: the whole state was replaced.
	 */
	UPROPERTY(BlueprintAssignable, Category = "Story")
	FStoryChangedSignature OnStoryChanged;

	/** A dialog or a level script triggered a story event */
	UPROPERTY(BlueprintAssignable, Category = "Story")
	FStoryEventSignature OnStoryEvent;

	virtual void Initialize(FSubsystemCollectionBase& Collection) override;

	/** Flag value, None when not set */
	UFUNCTION(BlueprintPure, Category = "Story")
	FName GetFlag(FName Id) const;

	/** Sets a flag, None clears it */
	UFUNCTION(BlueprintCallable, Category = "Story")
	void SetFlag(FName Id, FName Value);

	UFUNCTION(BlueprintPure, Category = "Story")
	bool GetBoolFlag(FName Id) const;

	UFUNCTION(BlueprintCallable, Category = "Story")
	void SetBoolFlag(FName Id, bool bValue);

	/** Current quest step, None when not started */
	UFUNCTION(BlueprintPure, Category = "Story")
	FName GetQuestStep(FName Id) const;

	UFUNCTION(BlueprintCallable, Category = "Story")
	void SetQuestStep(FName Id, FName Step);

	UFUNCTION(BlueprintPure, Category = "Story")
	bool HasStamp(FName Id) const;

	UFUNCTION(BlueprintCallable, Category = "Story")
	void AddStamp(FName Id);

	UFUNCTION(BlueprintPure, Category = "Story")
	int32 GetItemCount(FName Id) const;

	/** Adds Count of an item, a negative Count takes, never below zero */
	UFUNCTION(BlueprintCallable, Category = "Story")
	void AddItem(FName Id, int32 Count = 1);

	/** Broadcasts OnStoryEvent */
	UFUNCTION(BlueprintCallable, Category = "Story")
	void TriggerEvent(FName Event);

	/** True when every condition passes, also for an empty list */
	UFUNCTION(BlueprintPure, Category = "Story")
	bool CheckConditions(const TArray<FStoryCondition>& Conditions) const;

	UFUNCTION(BlueprintCallable, Category = "Story")
	void RunActions(const TArray<FStoryAction>& Actions);

	UFUNCTION(BlueprintPure, Category = "Story")
	const FStoryState& GetState() const { return State; }

	/** Replaces the whole state, for loading saves */
	UFUNCTION(BlueprintCallable, Category = "Story")
	void SetState(const FStoryState& NewState);

	UFUNCTION(BlueprintCallable, Category = "Story")
	void ResetState();

	/** Definition of an id, false when it is not defined */
	UFUNCTION(BlueprintPure, Category = "Story")
	bool FindDefinition(FName Id, FStoryIdRow& Definition) const;

	/** Sets the entry that the next dialogue starts with, None: default */
	UFUNCTION(BlueprintCallable, Category = "Story")
	void SetDialogueEntry(FName Entry) { DialogueEntry = Entry; }

	virtual FName GetParticipantName_Implementation() const override;

	virtual bool CheckCondition_Implementation(const UDlgContext* Context,
		FName ConditionName) const override;

	virtual int32 GetIntValue_Implementation(FName ValueName) const override;

	virtual bool GetBoolValue_Implementation(FName ValueName) const override;

	virtual FName GetNameValue_Implementation(FName ValueName) const override;

	virtual bool OnDialogueEvent_Implementation(UDlgContext* Context,
		FName EventName) override;

	virtual bool ModifyIntValue_Implementation(FName ValueName, bool bDelta,
		int32 Value) override;

	virtual bool ModifyBoolValue_Implementation(FName ValueName,
		bool bNewValue) override;

	virtual bool ModifyNameValue_Implementation(FName ValueName,
		FName NameValue) override;

	/** Every defined id with its value, plus values of undefined ids */
	TArray<FString> DescribeState() const;

	/** Sets any id by its definition: flag or quest value, stamp, count */
	bool SetById(FName Id, const FString& Value);

private:

	/** Warns when an id or its value is not defined */
	void Validate(EStoryIdKind Kind, FName Id, FName Value) const;

	void SetMapValue(TMap<FName, FName>& Map, EStoryIdKind Kind, FName Id,
		FName Value);
};
