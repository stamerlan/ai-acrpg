#include "StoryStateSubsystem.h"
#include "StorySettings.h"
#include "Engine/DataTable.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
#include "acrpg.h"

namespace
{
	const FName TrueValue(TEXT("true"));

	UStoryStateSubsystem* GetStory(const UWorld* World, FOutputDevice& Ar)
	{
		const UGameInstance* GameInstance =
			World ? World->GetGameInstance() : nullptr;
		UStoryStateSubsystem* Story = GameInstance
			? GameInstance->GetSubsystem<UStoryStateSubsystem>() : nullptr;
		if (!Story)
		{
			Ar.Log(TEXT("No story state, start the game first"));
		}
		return Story;
	}

	FAutoConsoleCommandWithWorldArgsAndOutputDevice StoryListCommand(
		TEXT("Story.List"),
		TEXT("Lists every quest, flag, stamp and item with its value"),
		FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World,
				FOutputDevice& Ar)
			{
				if (const UStoryStateSubsystem* Story = GetStory(World, Ar))
				{
					for (const FString& Line : Story->DescribeState())
					{
						Ar.Log(Line);
					}
				}
			}));

	FAutoConsoleCommandWithWorldArgsAndOutputDevice StorySetCommand(
		TEXT("Story.Set"),
		TEXT("Story.Set <id> [value]: sets a flag (no value: true, none: "
			"clear), a quest step, a stamp (none: remove) or an item count"),
		FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World,
				FOutputDevice& Ar)
			{
				UStoryStateSubsystem* Story = GetStory(World, Ar);
				if (!Story)
				{
					return;
				}
				if (Args.IsEmpty())
				{
					Ar.Log(TEXT("Usage: Story.Set <id> [value]"));
					return;
				}
				const FName Id(*Args[0]);
				if (!Story->SetById(Id, Args.IsValidIndex(1)
					? Args[1] : FString()))
				{
					Ar.Logf(TEXT("Unknown story id '%s'"), *Args[0]);
				}
			}));

	FAutoConsoleCommandWithWorldArgsAndOutputDevice StoryEventCommand(
		TEXT("Story.Event"),
		TEXT("Story.Event <name>: triggers a story event"),
		FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World,
				FOutputDevice& Ar)
			{
				UStoryStateSubsystem* Story = GetStory(World, Ar);
				if (Story && !Args.IsEmpty())
				{
					Story->TriggerEvent(FName(*Args[0]));
				}
			}));

	FAutoConsoleCommandWithWorldArgsAndOutputDevice StoryResetCommand(
		TEXT("Story.Reset"),
		TEXT("Clears the whole story state"),
		FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World,
				FOutputDevice& Ar)
			{
				if (UStoryStateSubsystem* Story = GetStory(World, Ar))
				{
					Story->ResetState();
				}
			}));
}

void UStoryStateSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	for (const TSoftObjectPtr<UDataTable>& TablePtr :
		GetDefault<UStorySettings>()->IdTables)
	{
		const UDataTable* Table = TablePtr.LoadSynchronous();
		if (!Table || Table->GetRowStruct() != FStoryIdRow::StaticStruct())
		{
			UE_LOG(Logacrpg, Error, TEXT("'%s' is not a story id table"),
				*TablePtr.ToString());
			continue;
		}
		Table->ForeachRow<FStoryIdRow>(TEXT("Story ids"),
			[this](const FName& Id, const FStoryIdRow& Row)
			{
				Definitions.Add(Id, Row);
			});
	}
}

FName UStoryStateSubsystem::GetFlag(FName Id) const
{
	const FName* Value = State.Flags.Find(Id);
	return Value ? *Value : NAME_None;
}

void UStoryStateSubsystem::SetFlag(FName Id, FName Value)
{
	SetMapValue(State.Flags, EStoryIdKind::Flag, Id, Value);
}

bool UStoryStateSubsystem::GetBoolFlag(FName Id) const
{
	return GetFlag(Id) == TrueValue;
}

void UStoryStateSubsystem::SetBoolFlag(FName Id, bool bValue)
{
	SetFlag(Id, bValue ? TrueValue : NAME_None);
}

FName UStoryStateSubsystem::GetQuestStep(FName Id) const
{
	const FName* Step = State.Quests.Find(Id);
	return Step ? *Step : NAME_None;
}

void UStoryStateSubsystem::SetQuestStep(FName Id, FName Step)
{
	SetMapValue(State.Quests, EStoryIdKind::Quest, Id, Step);
}

bool UStoryStateSubsystem::HasStamp(FName Id) const
{
	return State.Stamps.Contains(Id);
}

void UStoryStateSubsystem::AddStamp(FName Id)
{
	Validate(EStoryIdKind::Stamp, Id, NAME_None);
	if (!State.Stamps.Contains(Id))
	{
		State.Stamps.Add(Id);
		OnStoryChanged.Broadcast(EStoryIdKind::Stamp, Id, TrueValue);
	}
}

int32 UStoryStateSubsystem::GetItemCount(FName Id) const
{
	const int32* Count = State.Items.Find(Id);
	return Count ? *Count : 0;
}

void UStoryStateSubsystem::AddItem(FName Id, int32 Count)
{
	Validate(EStoryIdKind::Item, Id, NAME_None);
	const int32 NewCount = FMath::Max(0, GetItemCount(Id) + Count);
	if (NewCount == GetItemCount(Id))
	{
		return;
	}

	if (NewCount > 0)
	{
		State.Items.Add(Id, NewCount);
	}
	else
	{
		State.Items.Remove(Id);
	}
	OnStoryChanged.Broadcast(EStoryIdKind::Item, Id,
		FName(*FString::FromInt(NewCount)));
}

void UStoryStateSubsystem::TriggerEvent(FName Event)
{
	UE_LOG(Logacrpg, Log, TEXT("Story event '%s'"), *Event.ToString());
	OnStoryEvent.Broadcast(Event);
}

bool UStoryStateSubsystem::CheckConditions(
	const TArray<FStoryCondition>& Conditions) const
{
	for (const FStoryCondition& Condition : Conditions)
	{
		bool bPass = false;
		switch (Condition.Type)
		{
		case EStoryConditionType::FlagIs:
		case EStoryConditionType::FlagIsNot:
			bPass = (GetFlag(Condition.Id) == Condition.Value) ==
				(Condition.Type == EStoryConditionType::FlagIs);
			break;
		case EStoryConditionType::QuestIs:
		case EStoryConditionType::QuestIsNot:
			bPass = (GetQuestStep(Condition.Id) == Condition.Value) ==
				(Condition.Type == EStoryConditionType::QuestIs);
			break;
		case EStoryConditionType::HasItem:
		case EStoryConditionType::LacksItem:
			bPass = (GetItemCount(Condition.Id) >= Condition.Count) ==
				(Condition.Type == EStoryConditionType::HasItem);
			break;
		}
		if (!bPass)
		{
			return false;
		}
	}
	return true;
}

void UStoryStateSubsystem::RunActions(const TArray<FStoryAction>& Actions)
{
	for (const FStoryAction& Action : Actions)
	{
		switch (Action.Type)
		{
		case EStoryActionType::SetFlag:
			SetFlag(Action.Id, Action.Value);
			break;
		case EStoryActionType::SetQuest:
			SetQuestStep(Action.Id, Action.Value);
			break;
		case EStoryActionType::AddStamp:
			AddStamp(Action.Id);
			break;
		case EStoryActionType::GiveItem:
			AddItem(Action.Id, Action.Count);
			break;
		case EStoryActionType::TakeItem:
			AddItem(Action.Id, -Action.Count);
			break;
		case EStoryActionType::Event:
			TriggerEvent(Action.Id);
			break;
		}
	}
}

FName UStoryStateSubsystem::GetParticipantName_Implementation() const
{
	return TEXT("Story");
}

bool UStoryStateSubsystem::CheckCondition_Implementation(
	const UDlgContext* Context, FName ConditionName) const
{
	const FString Name = ConditionName.ToString();
	if (!Name.StartsWith(TEXT("entry_")))
	{
		UE_LOG(Logacrpg, Warning, TEXT("Unknown dialogue condition '%s'"),
			*Name);
		return false;
	}
	return !DialogueEntry.IsNone() &&
		Name.RightChop(6) == DialogueEntry.ToString();
}

int32 UStoryStateSubsystem::GetIntValue_Implementation(FName ValueName) const
{
	return GetItemCount(ValueName);
}

bool UStoryStateSubsystem::GetBoolValue_Implementation(FName ValueName) const
{
	const FStoryIdRow* Definition = Definitions.Find(ValueName);
	return Definition && Definition->Kind == EStoryIdKind::Stamp
		? HasStamp(ValueName) : GetBoolFlag(ValueName);
}

FName UStoryStateSubsystem::GetNameValue_Implementation(FName ValueName) const
{
	const FStoryIdRow* Definition = Definitions.Find(ValueName);
	return Definition && Definition->Kind == EStoryIdKind::Quest
		? GetQuestStep(ValueName) : GetFlag(ValueName);
}

bool UStoryStateSubsystem::OnDialogueEvent_Implementation(
	UDlgContext* Context, FName EventName)
{
	TriggerEvent(EventName);
	return true;
}

bool UStoryStateSubsystem::ModifyIntValue_Implementation(FName ValueName,
	bool bDelta, int32 Value)
{
	AddItem(ValueName, bDelta ? Value : Value - GetItemCount(ValueName));
	return true;
}

bool UStoryStateSubsystem::ModifyBoolValue_Implementation(FName ValueName,
	bool bNewValue)
{
	const FStoryIdRow* Definition = Definitions.Find(ValueName);
	if (Definition && Definition->Kind == EStoryIdKind::Stamp)
	{
		SetById(ValueName, bNewValue ? FString() : TEXT("none"));
	}
	else
	{
		SetBoolFlag(ValueName, bNewValue);
	}
	return true;
}

bool UStoryStateSubsystem::ModifyNameValue_Implementation(FName ValueName,
	FName NameValue)
{
	const FStoryIdRow* Definition = Definitions.Find(ValueName);
	if (Definition && Definition->Kind == EStoryIdKind::Quest)
	{
		SetQuestStep(ValueName, NameValue);
	}
	else
	{
		SetFlag(ValueName, NameValue);
	}
	return true;
}

void UStoryStateSubsystem::SetState(const FStoryState& NewState)
{
	State = NewState;
	OnStoryChanged.Broadcast(EStoryIdKind::Quest, NAME_None, NAME_None);
}

void UStoryStateSubsystem::ResetState()
{
	SetState(FStoryState());
}

bool UStoryStateSubsystem::FindDefinition(FName Id,
	FStoryIdRow& Definition) const
{
	const FStoryIdRow* Found = Definitions.Find(Id);
	if (Found)
	{
		Definition = *Found;
	}
	return Found != nullptr;
}

TArray<FString> UStoryStateSubsystem::DescribeState() const
{
	TArray<FString> Lines;
	auto Describe = [this, &Lines](EStoryIdKind Kind, FName Id)
	{
		FString Value;
		switch (Kind)
		{
		case EStoryIdKind::Quest:
			Value = GetQuestStep(Id).ToString();
			break;
		case EStoryIdKind::Flag:
			Value = GetFlag(Id).ToString();
			break;
		case EStoryIdKind::Stamp:
			Value = HasStamp(Id) ? TEXT("set") : TEXT("None");
			break;
		case EStoryIdKind::Item:
			Value = FString::FromInt(GetItemCount(Id));
			break;
		}
		const FStoryIdRow* Definition = Definitions.Find(Id);
		Lines.Add(FString::Printf(TEXT("%-8s %-24s = %-12s %s"),
			*StaticEnum<EStoryIdKind>()->GetNameStringByValue(
				static_cast<int64>(Kind)),
			*Id.ToString(), *Value,
			Definition ? *Definition->Description : TEXT("(undefined)")));
	};

	for (const TPair<FName, FStoryIdRow>& Definition : Definitions)
	{
		Describe(Definition.Value.Kind, Definition.Key);
	}
	for (const TPair<FName, FName>& Quest : State.Quests)
	{
		if (!Definitions.Contains(Quest.Key))
		{
			Describe(EStoryIdKind::Quest, Quest.Key);
		}
	}
	for (const TPair<FName, FName>& Flag : State.Flags)
	{
		if (!Definitions.Contains(Flag.Key))
		{
			Describe(EStoryIdKind::Flag, Flag.Key);
		}
	}
	for (const FName& Stamp : State.Stamps)
	{
		if (!Definitions.Contains(Stamp))
		{
			Describe(EStoryIdKind::Stamp, Stamp);
		}
	}
	for (const TPair<FName, int32>& Item : State.Items)
	{
		if (!Definitions.Contains(Item.Key))
		{
			Describe(EStoryIdKind::Item, Item.Key);
		}
	}
	return Lines;
}

bool UStoryStateSubsystem::SetById(FName Id, const FString& Value)
{
	const FStoryIdRow* Definition = Definitions.Find(Id);
	if (!Definition)
	{
		return false;
	}

	const bool bClear = Value.Equals(TEXT("none"), ESearchCase::IgnoreCase);
	switch (Definition->Kind)
	{
	case EStoryIdKind::Quest:
		SetQuestStep(Id, bClear ? NAME_None : FName(*Value));
		break;
	case EStoryIdKind::Flag:
		SetFlag(Id, bClear ? NAME_None
			: Value.IsEmpty() ? TrueValue : FName(*Value));
		break;
	case EStoryIdKind::Stamp:
		if (!bClear)
		{
			AddStamp(Id);
		}
		else if (State.Stamps.Remove(Id) > 0)
		{
			OnStoryChanged.Broadcast(EStoryIdKind::Stamp, Id, NAME_None);
		}
		break;
	case EStoryIdKind::Item:
		AddItem(Id, (Value.IsEmpty() ? 1 : FCString::Atoi(*Value)) -
			GetItemCount(Id));
		break;
	}
	return true;
}

void UStoryStateSubsystem::Validate(EStoryIdKind Kind, FName Id,
	FName Value) const
{
	const FStoryIdRow* Definition = Definitions.Find(Id);
	if (!Definition || Definition->Kind != Kind)
	{
		UE_LOG(Logacrpg, Warning, TEXT("Story id '%s' is not a defined %s"),
			*Id.ToString(), *StaticEnum<EStoryIdKind>()->
				GetNameStringByValue(static_cast<int64>(Kind)));
		return;
	}

	const bool bBoolFlag =
		Kind == EStoryIdKind::Flag && Definition->Values.IsEmpty();
	const bool bValid = Value.IsNone() ||
		(bBoolFlag ? Value == TrueValue : Definition->Values.Contains(Value));
	if (!bValid)
	{
		UE_LOG(Logacrpg, Warning, TEXT("'%s' is not a value of '%s'"),
			*Value.ToString(), *Id.ToString());
	}
}

void UStoryStateSubsystem::SetMapValue(TMap<FName, FName>& Map,
	EStoryIdKind Kind, FName Id, FName Value)
{
	Validate(Kind, Id, Value);
	const FName* Current = Map.Find(Id);
	if ((Current ? *Current : NAME_None) == Value)
	{
		return;
	}

	if (Value.IsNone())
	{
		Map.Remove(Id);
	}
	else
	{
		Map.Add(Id, Value);
	}
	UE_LOG(Logacrpg, Log, TEXT("Story: %s = %s"), *Id.ToString(),
		*Value.ToString());
	OnStoryChanged.Broadcast(Kind, Id, Value);
}
