#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "StorySettings.generated.h"

class UDataTable;

/** Project settings of the story state, under Game > Story */
UCLASS(config = Game, defaultconfig, meta = (DisplayName = "Story"))
class UStorySettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:

	/** Tables of FStoryIdRow that define every quest, flag, stamp, item */
	UPROPERTY(config, EditAnywhere, Category = "Story")
	TArray<TSoftObjectPtr<UDataTable>> IdTables;

	virtual FName GetCategoryName() const override { return TEXT("Game"); }
};
