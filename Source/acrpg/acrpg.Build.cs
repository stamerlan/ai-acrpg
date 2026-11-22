// Copyright Epic Games, Inc. All Rights Reserved.

using UnrealBuildTool;

public class acrpg : ModuleRules
{
	public acrpg(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core",
			"CoreUObject",
			"Engine",
			"InputCore",
			"EnhancedInput",
			"AIModule",
			"NavigationSystem",
			"StateTreeModule",
			"GameplayStateTreeModule",
			"Niagara",
			"UMG",
			"Slate"
		});

		PrivateDependencyModuleNames.AddRange(new string[] { });

		PublicIncludePaths.AddRange(new string[] {
			"acrpg",
			"acrpg/Protagonist",
			"acrpg/Variant_Strategy",
			"acrpg/Variant_Strategy/UI",
			"acrpg/Variant_TwinStick",
			"acrpg/Variant_TwinStick/AI",
			"acrpg/Variant_TwinStick/Gameplay",
			"acrpg/Variant_TwinStick/UI"
		});

		// Uncomment if you are using Slate UI
		// PrivateDependencyModuleNames.AddRange(new string[] { "Slate", "SlateCore" });

		// Uncomment if you are using online features
		// PrivateDependencyModuleNames.Add("OnlineSubsystem");

		// To include OnlineSubsystemSteam, add it to the plugins section in your uproject file with the Enabled attribute set to true
	}
}
