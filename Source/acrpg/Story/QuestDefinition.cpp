#include "QuestDefinition.h"
#include "AssetRegistry/AssetRegistryModule.h"

bool UQuestDefinition::FindStep(FName Step, FText& Text,
	bool& bFinished) const
{
	for (const FQuestStepText& Entry : Steps)
	{
		if (Entry.Step == Step)
		{
			Text = Entry.Text;
			bFinished = Entry.bFinished;
			return true;
		}
	}
	Text = FText::GetEmpty();
	bFinished = false;
	return false;
}

TArray<UQuestDefinition*> UQuestDefinition::GetAllQuests()
{
	// The asset manager cooks every asset in /Game/Story/Quests
	// (DefaultGame.ini), so the registry lists them in packaged builds too
	TArray<FAssetData> Assets;
	IAssetRegistry::GetChecked().GetAssetsByClass(
		StaticClass()->GetClassPathName(), Assets, true);

	TArray<UQuestDefinition*> Quests;
	for (const FAssetData& Asset : Assets)
	{
		if (UQuestDefinition* Quest = Cast<UQuestDefinition>(Asset.GetAsset()))
		{
			Quests.Add(Quest);
		}
	}
	Quests.Sort([](const UQuestDefinition& A, const UQuestDefinition& B)
	{
		return A.bMain != B.bMain ? A.bMain : A.SortOrder < B.SortOrder;
	});
	return Quests;
}
