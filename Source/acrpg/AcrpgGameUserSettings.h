#pragma once

#include "CoreMinimal.h"
#include "GameFramework/GameUserSettings.h"
#include "AcrpgGameUserSettings.generated.h"

/** How the player rotates the camera around the chicken */
UENUM(BlueprintType)
enum class ECameraRotationStyle : uint8
{
	/** Rotation snaps in fixed steps (45 degrees by default) */
	Stepped,

	/** Rotation is continuous */
	Free
};

/**
 *  Player settings saved to GameUserSettings.ini.
 *  Registered with GameUserSettingsClassName in DefaultEngine.ini.
 */
UCLASS()
class UAcrpgGameUserSettings : public UGameUserSettings
{
	GENERATED_BODY()

public:

	/** Camera rotation style. Fixed steps or free is an open question. */
	UPROPERTY(Config, BlueprintReadWrite, Category = "Camera")
	ECameraRotationStyle CameraRotationStyle = ECameraRotationStyle::Stepped;

	/** Returns the settings object of the running game */
	UFUNCTION(BlueprintPure, Category = "Settings")
	static UAcrpgGameUserSettings* GetAcrpgGameUserSettings();
};
