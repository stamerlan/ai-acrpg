#include "AcrpgGameUserSettings.h"
#include "Engine/Engine.h"

UAcrpgGameUserSettings* UAcrpgGameUserSettings::GetAcrpgGameUserSettings()
{
	return GEngine
		? Cast<UAcrpgGameUserSettings>(GEngine->GetGameUserSettings())
		: nullptr;
}
