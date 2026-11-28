#include "SaveSubsystem.h"
#include "AcrpgSaveGame.h"
#include "CheckpointSubsystem.h"
#include "StorySettings.h"
#include "StoryStateSubsystem.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "Misc/PackageName.h"
#include "acrpg.h"

namespace
{
	const FString SlotName(TEXT("Checkpoint"));

	/** The save the last write replaced */
	const FString BackupSlotName(TEXT("Checkpoint_Prev"));

	const FString NoFile(TEXT("no file"));

	/**
	 *  Loads a slot. Returns the save when this build can use it, null
	 *  otherwise; State says what is in the file either way.
	 */
	UAcrpgSaveGame* LoadSlot(const FString& Slot, FString& State)
	{
		if (!UGameplayStatics::DoesSaveGameExist(Slot, 0))
		{
			State = NoFile;
			return nullptr;
		}
		UAcrpgSaveGame* Save = Cast<UAcrpgSaveGame>(
			UGameplayStatics::LoadGameFromSlot(Slot, 0));
		if (!Save)
		{
			State = TEXT("can't be read, ignored");
			return nullptr;
		}
		if (Save->SaveVersion != UAcrpgSaveGame::CurrentVersion)
		{
			State = FString::Printf(
				TEXT("version %d, this build reads %d: ignored"),
				Save->SaveVersion, UAcrpgSaveGame::CurrentVersion);
			return nullptr;
		}
		if (!FPackageName::DoesPackageExist(Save->Checkpoint.Map))
		{
			State = FString::Printf(
				TEXT("version %d, map '%s' doesn't exist: ignored"),
				Save->SaveVersion, *Save->Checkpoint.Map);
			return nullptr;
		}
		State = FString::Printf(TEXT("version %d, saved %s: %s"),
			Save->SaveVersion, *Save->SavedAt.ToString(),
			*UCheckpointSubsystem::Describe(Save->Checkpoint));
		return Save;
	}

	USaveSubsystem* GetSaves(const UWorld* World, FOutputDevice& Ar)
	{
		const UGameInstance* GameInstance =
			World ? World->GetGameInstance() : nullptr;
		USaveSubsystem* Saves = GameInstance
			? GameInstance->GetSubsystem<USaveSubsystem>() : nullptr;
		if (!Saves)
		{
			Ar.Log(TEXT("No saves, start the game first"));
		}
		return Saves;
	}

	FAutoConsoleCommandWithWorldArgsAndOutputDevice InfoCommand(
		TEXT("Save.Info"),
		TEXT("Shows the save Continue loads and the save files"),
		FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World,
				FOutputDevice& Ar)
			{
				if (const USaveSubsystem* Saves = GetSaves(World, Ar))
				{
					for (const FString& Line : Saves->Describe())
					{
						Ar.Log(Line);
					}
				}
			}));

	FAutoConsoleCommandWithWorldArgsAndOutputDevice ContinueCommand(
		TEXT("Save.Continue"),
		TEXT("Loads the save on disk, as Continue in the main menu"),
		FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World,
				FOutputDevice& Ar)
			{
				if (USaveSubsystem* Saves = GetSaves(World, Ar))
				{
					Saves->Continue(World);
				}
			}));

	FAutoConsoleCommandWithWorldArgsAndOutputDevice DeleteCommand(
		TEXT("Save.Delete"),
		TEXT("Deletes the save and its backup, the game in memory goes on"),
		FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World,
				FOutputDevice& Ar)
			{
				if (USaveSubsystem* Saves = GetSaves(World, Ar))
				{
					Saves->DeleteSave();
				}
			}));
}

void USaveSubsystem::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);

	for (const FString& Slot : {SlotName, BackupSlotName})
	{
		FString State;
		Current = LoadSlot(Slot, State);
		if (Current)
		{
			UE_LOG(Logacrpg, Log, TEXT("Save '%s' found: %s"), *Slot,
				*State);
			return;
		}
		if (State != NoFile)
		{
			UE_LOG(Logacrpg, Warning, TEXT("Save '%s' %s"), *Slot, *State);
		}
	}
}

void USaveSubsystem::Continue(const UObject* WorldContext)
{
	UCheckpointSubsystem* Checkpoints =
		GetGameInstance()->GetSubsystem<UCheckpointSubsystem>();
	if (!Current || !Checkpoints)
	{
		UE_LOG(Logacrpg, Warning, TEXT("No save to continue"));
		return;
	}

	bSessionStarted = true;
	UE_LOG(Logacrpg, Log, TEXT("Continue: %s"),
		*UCheckpointSubsystem::Describe(Current->Checkpoint));
	Checkpoints->SetLastCheckpoint(Current->Checkpoint);
	Checkpoints->ReloadLastCheckpoint(WorldContext);
}

void USaveSubsystem::NewGame(const UObject* WorldContext)
{
	const UWorld* World = GEngine->GetWorldFromContextObject(WorldContext,
		EGetWorldErrorMode::LogAndReturnNull);
	const TSoftObjectPtr<UWorld>& Map =
		GetDefault<UStorySettings>()->NewGameMap;
	if (!World || Map.IsNull())
	{
		UE_LOG(Logacrpg, Error, TEXT("Can't start a new game: no world or "
			"no New Game Map in Project Settings > Game > Story"));
		return;
	}

	DeleteSave();
	bSessionStarted = true;
	if (UCheckpointSubsystem* Checkpoints =
		GetGameInstance()->GetSubsystem<UCheckpointSubsystem>())
	{
		Checkpoints->ResetCheckpoints();
	}
	if (UStoryStateSubsystem* Story =
		GetGameInstance()->GetSubsystem<UStoryStateSubsystem>())
	{
		Story->ResetState();
	}

	UE_LOG(Logacrpg, Log, TEXT("New game in %s"), *Map.ToString());
	UGameplayStatics::OpenLevelBySoftObjectPtr(World, Map);
}

void USaveSubsystem::DeleteSave()
{
	for (const FString& Slot : {SlotName, BackupSlotName})
	{
		if (UGameplayStatics::DeleteGameInSlot(Slot, 0))
		{
			UE_LOG(Logacrpg, Log, TEXT("Save '%s' deleted"), *Slot);
		}
	}
	Current = nullptr;
}

void USaveSubsystem::WriteSave(const FCheckpointSnapshot& Snapshot,
	bool bArrival)
{
	const bool bGameplayMap = GetDefault<UStorySettings>()->SavedMapPrefixes
		.ContainsByPredicate([&Snapshot](const FString& Prefix)
		{
			return Snapshot.Map.StartsWith(Prefix);
		});
	if (!bGameplayMap)
	{
		UE_LOG(Logacrpg, Log, TEXT("%s is not a gameplay map (Saved Map "
			"Prefixes in Project Settings > Game > Story): not saved to disk"),
			*Snapshot.Map);
		return;
	}
	if (bArrival && !bSessionStarted && Current)
	{
		UE_LOG(Logacrpg, Log, TEXT("Play started in %s without Continue or "
			"New game: its LevelStart doesn't replace the save"),
			*Snapshot.Map);
		return;
	}
	bSessionStarted = true;

	// The save being replaced is the backup if the new file turns out bad
	if (Current
		&& !UGameplayStatics::SaveGameToSlot(Current, BackupSlotName, 0))
	{
		UE_LOG(Logacrpg, Warning, TEXT("Writing backup save '%s' failed"),
			*BackupSlotName);
	}

	UAcrpgSaveGame* Save = NewObject<UAcrpgSaveGame>(this);
	Save->SaveVersion = UAcrpgSaveGame::CurrentVersion;
	Save->SavedAt = FDateTime::Now();
	Save->Checkpoint = Snapshot;
	if (!UGameplayStatics::SaveGameToSlot(Save, SlotName, 0))
	{
		UE_LOG(Logacrpg, Error, TEXT("Writing save '%s' failed"), *SlotName);
		return;
	}
	Current = Save;
	UE_LOG(Logacrpg, Log, TEXT("Saved to disk: %s"),
		*UCheckpointSubsystem::Describe(Snapshot));
}

TArray<FString> USaveSubsystem::Describe() const
{
	TArray<FString> Lines;
	Lines.Add(Current
		? FString::Printf(TEXT("Continue loads the save of %s: %s"),
			*Current->SavedAt.ToString(),
			*UCheckpointSubsystem::Describe(Current->Checkpoint))
		: FString(TEXT("Continue is off: no usable save")));
	for (const FString& Slot : {SlotName, BackupSlotName})
	{
		FString State;
		LoadSlot(Slot, State);
		Lines.Add(FString::Printf(TEXT("File '%s': %s"), *Slot, *State));
	}
	return Lines;
}
