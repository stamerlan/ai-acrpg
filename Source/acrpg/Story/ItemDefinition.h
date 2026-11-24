#pragma once

#include "CoreMinimal.h"
#include "Engine/DataAsset.h"
#include "ItemDefinition.generated.h"

class UTexture2D;

/** Fixed section of the backpack an item is shown in */
UENUM(BlueprintType)
enum class EItemSection : uint8
{
	/** The shotgun, shells and corn */
	Gear,
	/** The checklist, the transit card, keys, quest items */
	KeyItem,
	/** Collectibles with funny descriptions */
	Joke
};

/**
 *  What the backpack knows about an inventory item. The story state only
 *  counts items by id; this asset adds the name, picture and description.
 *  One asset per item id, in /Game/Items (DA_Item_<Name>).
 */
UCLASS(BlueprintType)
class UItemDefinition : public UPrimaryDataAsset
{
	GENERATED_BODY()

public:

	/** Story item id, for example item_corn_cob */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Item")
	FName Id;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Item")
	FText DisplayName;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Item",
		meta = (MultiLine = true))
	FText Description;

	/** Square picture shown in the backpack */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Item")
	TObjectPtr<UTexture2D> Picture;

	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Item")
	EItemSection Section = EItemSection::KeyItem;

	/** Fixed place in its section, lower first */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Item")
	int32 SortOrder = 0;

	/** Most she can carry, 0 for no limit. Adding more is ignored. */
	UPROPERTY(EditAnywhere, BlueprintReadOnly, Category = "Item",
		meta = (ClampMin = 0))
	int32 MaxCount = 0;

	/** Every item definition, by section and then by sort order */
	UFUNCTION(BlueprintCallable, Category = "Item")
	static TArray<UItemDefinition*> GetAllItems();

	/** The definition of a story item id, None if there is none */
	UFUNCTION(BlueprintCallable, Category = "Item")
	static UItemDefinition* FindItem(FName ItemId);
};
