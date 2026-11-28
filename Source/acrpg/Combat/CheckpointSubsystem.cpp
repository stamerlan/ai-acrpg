#include "CheckpointSubsystem.h"
#include "SaveSubsystem.h"
#include "StoryStateSubsystem.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "Engine/World.h"
#include "HAL/IConsoleManager.h"
#include "Kismet/GameplayStatics.h"
#include "acrpg.h"

namespace
{
	const FName LevelStartId(TEXT("LevelStart"));

	UCheckpointSubsystem* GetCheckpoints(const UWorld* World,
		FOutputDevice& Ar)
	{
		const UGameInstance* GameInstance =
			World ? World->GetGameInstance() : nullptr;
		UCheckpointSubsystem* Checkpoints = GameInstance
			? GameInstance->GetSubsystem<UCheckpointSubsystem>() : nullptr;
		if (!Checkpoints)
		{
			Ar.Log(TEXT("No checkpoints, start the game first"));
		}
		return Checkpoints;
	}

	FAutoConsoleCommandWithWorldArgsAndOutputDevice ReloadCommand(
		TEXT("Checkpoint.Reload"),
		TEXT("Reloads the last checkpoint"),
		FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World,
				FOutputDevice& Ar)
			{
				if (UCheckpointSubsystem* Checkpoints =
					GetCheckpoints(World, Ar))
				{
					Checkpoints->ReloadLastCheckpoint(World);
				}
			}));

	FAutoConsoleCommandWithWorldArgsAndOutputDevice InfoCommand(
		TEXT("Checkpoint.Info"),
		TEXT("Shows the last checkpoint"),
		FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World,
				FOutputDevice& Ar)
			{
				if (const UCheckpointSubsystem* Checkpoints =
					GetCheckpoints(World, Ar))
				{
					Ar.Log(Checkpoints->HasCheckpoint()
						? UCheckpointSubsystem::Describe(
							Checkpoints->GetLastCheckpoint())
						: FString(TEXT("No checkpoint")));
				}
			}));
}

void UCheckpointSubsystem::SaveCheckpoint(const UObject* WorldContext,
	FName CheckpointId, const FTransform& PlayerTransform, float Health,
	FName Phase)
{
	const UWorld* World = GEngine->GetWorldFromContextObject(WorldContext,
		EGetWorldErrorMode::LogAndReturnNull);
	if (!World)
	{
		return;
	}
	UpdateDefeatedMap(World);

	Last.CheckpointId = CheckpointId;
	Last.Map = GetMapName(World);
	Last.Phase = Phase;
	Last.PlayerTransform = PlayerTransform;
	Last.Health = Health;
	Last.Defeated = Defeated;
	const UStoryStateSubsystem* Story =
		GetGameInstance()->GetSubsystem<UStoryStateSubsystem>();
	Last.Story = Story ? Story->GetState() : FStoryState();
	bHasCheckpoint = true;

	UE_LOG(Logacrpg, Log, TEXT("Checkpoint saved: %s"), *Describe(Last));
	if (USaveSubsystem* Saves =
		GetGameInstance()->GetSubsystem<USaveSubsystem>())
	{
		Saves->WriteSave(Last, CheckpointId == LevelStartId);
	}
}

void UCheckpointSubsystem::ReloadLastCheckpoint(const UObject* WorldContext)
{
	const UWorld* World = GEngine->GetWorldFromContextObject(WorldContext,
		EGetWorldErrorMode::LogAndReturnNull);
	if (!World)
	{
		return;
	}
	if (!bHasCheckpoint)
	{
		UE_LOG(Logacrpg, Warning,
			TEXT("No checkpoint yet, restarting the map"));
		UGameplayStatics::OpenLevel(World, FName(*GetMapName(World)));
		return;
	}

	if (UStoryStateSubsystem* Story =
		GetGameInstance()->GetSubsystem<UStoryStateSubsystem>())
	{
		Story->SetState(Last.Story);
	}
	Defeated = Last.Defeated;
	DefeatedMap = Last.Map;
	bPendingRestore = true;

	UE_LOG(Logacrpg, Log, TEXT("Reloading checkpoint: %s"), *Describe(Last));
	UGameplayStatics::OpenLevel(World, FName(*Last.Map));
}

bool UCheckpointSubsystem::OnPlayerBeginPlay(AActor* Player, float Health,
	float& RestoredHealth)
{
	RestoredHealth = Health;
	const UWorld* World = Player ? Player->GetWorld() : nullptr;
	if (!World)
	{
		return false;
	}
	UpdateDefeatedMap(World);

	const FString Map = GetMapName(World);
	const bool bRestore = bPendingRestore && bHasCheckpoint
		&& Last.Map == Map;
	bPendingRestore = false;
	if (bRestore)
	{
		Player->TeleportTo(Last.PlayerTransform.GetLocation(),
			Last.PlayerTransform.Rotator());
		RestoredHealth = Last.Health;
		return true;
	}

	if (!bHasCheckpoint || Last.Map != Map)
	{
		SaveCheckpoint(Player, LevelStartId, Player->GetActorTransform(),
			Health, NAME_None);
	}
	return false;
}

void UCheckpointSubsystem::MarkDefeated(const AActor* Actor)
{
	if (Actor)
	{
		UpdateDefeatedMap(Actor->GetWorld());
		Defeated.Add(Actor->GetFName());
	}
}

bool UCheckpointSubsystem::IsDefeated(const AActor* Actor) const
{
	return Actor && DefeatedMap == GetMapName(Actor->GetWorld())
		&& Defeated.Contains(Actor->GetFName());
}

void UCheckpointSubsystem::SetLastCheckpoint(
	const FCheckpointSnapshot& Snapshot)
{
	Last = Snapshot;
	bHasCheckpoint = true;
}

void UCheckpointSubsystem::ResetCheckpoints()
{
	Last = FCheckpointSnapshot();
	bHasCheckpoint = false;
	bPendingRestore = false;
	Defeated.Reset();
	DefeatedMap.Reset();
}

FString UCheckpointSubsystem::Describe(const FCheckpointSnapshot& Snapshot)
{
	return FString::Printf(TEXT("%s in %s, phase %s, at %s, health %.0f, "
		"%d defeated, %d quests, %d flags, %d stamps, %d items"),
		*Snapshot.CheckpointId.ToString(), *Snapshot.Map,
		*Snapshot.Phase.ToString(),
		*Snapshot.PlayerTransform.GetLocation().ToCompactString(),
		Snapshot.Health, Snapshot.Defeated.Num(), Snapshot.Story.Quests.Num(),
		Snapshot.Story.Flags.Num(), Snapshot.Story.Stamps.Num(),
		Snapshot.Story.Items.Num());
}

FString UCheckpointSubsystem::GetMapName(const UWorld* World)
{
	return World
		? UWorld::RemovePIEPrefix(World->GetOutermost()->GetName())
		: FString();
}

void UCheckpointSubsystem::UpdateDefeatedMap(const UWorld* World)
{
	const FString Map = GetMapName(World);
	if (Map != DefeatedMap)
	{
		Defeated.Reset();
		DefeatedMap = Map;
	}
}
