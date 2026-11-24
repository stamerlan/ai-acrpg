// Copyright Epic Games, Inc. All Rights Reserved.

#include "acrpg.h"
#include "Modules/ModuleManager.h"

#if WITH_EDITOR
#include "Animation/Skeleton.h"
#include "HAL/IConsoleManager.h"
#endif

IMPLEMENT_PRIMARY_GAME_MODULE( FDefaultGameModuleImpl, acrpg, "acrpg" );

DEFINE_LOG_CATEGORY(Logacrpg)

#if WITH_EDITOR
namespace
{
	// The Anim Slot Manager has no scripting API. A slot in its own group
	// plays montages without stopping those of the other groups (the
	// chicken eats on UpperBody while the kneel holds on DefaultSlot).
	FAutoConsoleCommandWithArgsAndOutputDevice SetSlotGroupCommand(
		TEXT("Acrpg.SetSlotGroup"),
		TEXT("Acrpg.SetSlotGroup <skeleton path> <slot> <group>: moves the "
			"slot into the group (made if missing); save the skeleton after"),
		FConsoleCommandWithArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, FOutputDevice& Ar)
			{
				USkeleton* Skeleton = Args.Num() == 3
					? LoadObject<USkeleton>(nullptr, *Args[0]) : nullptr;
				if (!Skeleton)
				{
					Ar.Log(TEXT("Usage: Acrpg.SetSlotGroup <skeleton path> "
						"<slot> <group>"));
					return;
				}
				Skeleton->Modify();
				Skeleton->SetSlotGroupName(FName(*Args[1]), FName(*Args[2]));
				Ar.Logf(TEXT("%s: slot %s is in group %s"), *Skeleton->GetName(),
					*Args[1],
					*Skeleton->GetSlotGroupName(FName(*Args[1])).ToString());
			}));
}
#endif
 