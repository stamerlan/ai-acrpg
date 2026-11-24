#include "ItemDefinition.h"
#include "AssetRegistry/AssetRegistryModule.h"

TArray<UItemDefinition*> UItemDefinition::GetAllItems()
{
	// The asset manager cooks every asset in /Game/Items (DefaultGame.ini),
	// so the registry lists them in packaged builds too
	TArray<FAssetData> Assets;
	IAssetRegistry::GetChecked().GetAssetsByClass(
		StaticClass()->GetClassPathName(), Assets, true);

	TArray<UItemDefinition*> Items;
	for (const FAssetData& Asset : Assets)
	{
		if (UItemDefinition* Item = Cast<UItemDefinition>(Asset.GetAsset()))
		{
			Items.Add(Item);
		}
	}
	Items.Sort([](const UItemDefinition& A, const UItemDefinition& B)
	{
		return A.Section != B.Section ? A.Section < B.Section
			: A.SortOrder < B.SortOrder;
	});
	return Items;
}

UItemDefinition* UItemDefinition::FindItem(FName ItemId)
{
	for (UItemDefinition* Item : GetAllItems())
	{
		if (Item->Id == ItemId)
		{
			return Item;
		}
	}
	return nullptr;
}
