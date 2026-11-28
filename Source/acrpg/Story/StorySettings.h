#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "StorySettings.generated.h"

class UDataTable;
class UWorld;

/** Project settings of the story state, under Game > Story */
UCLASS(config = Game, defaultconfig, meta = (DisplayName = "Story"))
class UStorySettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:

	/** Tables of FStoryIdRow that define every quest, flag, stamp, item */
	UPROPERTY(config, EditAnywhere, Category = "Story")
	TArray<TSoftObjectPtr<UDataTable>> IdTables;

	/** Map that New game in the main menu opens */
	UPROPERTY(config, EditAnywhere, Category = "Story")
	TSoftObjectPtr<UWorld> NewGameMap;

	/**
	 *  Gameplay maps: only checkpoints in a map whose long package name
	 *  starts with one of these are saved to disk (not the menu, dev maps)
	 */
	UPROPERTY(config, EditAnywhere, Category = "Story")
	TArray<FString> SavedMapPrefixes;

	virtual FName GetCategoryName() const override { return TEXT("Game"); }
};
