// Copyright Epic Games, Inc. All Rights Reserved.

#include "acrpg.h"
#include "Modules/ModuleManager.h"

#if WITH_EDITOR
#include "Animation/Skeleton.h"
#include "DlgSystem/DlgDialogue.h"
#include "DlgSystem/DlgSystemSettings.h"
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
				Ar.Logf(TEXT("%s: slot %s is in group %s"),
					*Skeleton->GetName(), *Args[1],
					*Skeleton->GetSlotGroupName(FName(*Args[1])).ToString());
			}));

	// DlgSystem nodes have no scripting API, and its text format is off
	// (the DLG_ assets are the only copy). These two commands write a
	// dialogue to <asset>.dlg.json next to it and read it back, so a
	// script can edit the JSON in between. Delete the JSON after.
	UDlgDialogue* LoadDialogue(const TArray<FString>& Args, FOutputDevice& Ar,
		const TCHAR* Usage)
	{
		UDlgDialogue* Dialogue = Args.Num() == 1
			? LoadObject<UDlgDialogue>(nullptr, *Args[0]) : nullptr;
		if (!Dialogue)
		{
			Ar.Log(Usage);
		}
		return Dialogue;
	}

	FAutoConsoleCommandWithArgsAndOutputDevice DlgExportCommand(
		TEXT("Acrpg.DlgExport"),
		TEXT("Acrpg.DlgExport <dialogue path>: writes the dialogue to a "
			".dlg.json file next to the asset"),
		FConsoleCommandWithArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, FOutputDevice& Ar)
			{
				const UDlgDialogue* Dialogue = LoadDialogue(Args, Ar,
					TEXT("Usage: Acrpg.DlgExport <dialogue path>"));
				if (!Dialogue)
				{
					return;
				}
				UDlgSystemSettings* Settings =
					GetMutableDefault<UDlgSystemSettings>();
				const EDlgDialogueTextFormat Old = Settings->DialogueTextFormat;
				Settings->DialogueTextFormat = EDlgDialogueTextFormat::JSON;
				Dialogue->ExportToFile();
				Ar.Logf(TEXT("Exported %s to %s"), *Dialogue->GetName(),
					*Dialogue->GetTextFilePathName());
				Settings->DialogueTextFormat = Old;
			}));

	FAutoConsoleCommandWithArgsAndOutputDevice DlgImportCommand(
		TEXT("Acrpg.DlgImport"),
		TEXT("Acrpg.DlgImport <dialogue path>: replaces the dialogue with "
			"its .dlg.json file and rebuilds the graph; save it after"),
		FConsoleCommandWithArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, FOutputDevice& Ar)
			{
				UDlgDialogue* Dialogue = LoadDialogue(Args, Ar,
					TEXT("Usage: Acrpg.DlgImport <dialogue path>"));
				if (!Dialogue)
				{
					return;
				}
				UDlgSystemSettings* Settings =
					GetMutableDefault<UDlgSystemSettings>();
				const EDlgDialogueTextFormat Old = Settings->DialogueTextFormat;
				Settings->DialogueTextFormat = EDlgDialogueTextFormat::JSON;
				Dialogue->Modify();
				Dialogue->ImportFromFile();
				Settings->DialogueTextFormat = Old;
				// Rebuilds the graph nodes from the imported dialogue nodes
				Dialogue->ClearGraph();
				Dialogue->MarkPackageDirty();
				Ar.Logf(TEXT("Imported %s: %d nodes"), *Dialogue->GetName(),
					Dialogue->GetNodes().Num());
			}));
}
#endif
 