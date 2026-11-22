#pragma once

#include "CoreMinimal.h"
#include "GameFramework/PlayerController.h"
#include "ProtagonistController.generated.h"

class UInputAction;
class UInputMappingContext;
class AProtagonistCharacter;
struct FInputActionValue;
struct FInputActionInstance;

/** The input device the player used last */
UENUM(BlueprintType)
enum class EAcrpgInputDevice : uint8
{
	KeyboardMouse,
	Gamepad
};

/** Which mapping context is active */
UENUM(BlueprintType)
enum class EAcrpgInputContext : uint8
{
	Gameplay,
	Dialog,
	Menu
};

DECLARE_DYNAMIC_MULTICAST_DELEGATE_OneParam(FInputDeviceChangedSignature,
	EAcrpgInputDevice, Device);

/**
 *  Player controller for the protagonist.
 *  Switches the gameplay, dialog and menu mapping contexts, drives the
 *  camera yaw (as the control rotation) and zoom, aims with the mouse
 *  cursor or the right stick, and tracks the last used input device.
 */
UCLASS(abstract)
class AProtagonistController : public APlayerController
{
	GENERATED_BODY()

protected:

	UPROPERTY(EditAnywhere, Category = "Input|Contexts")
	TObjectPtr<UInputMappingContext> GameplayMappingContext;

	UPROPERTY(EditAnywhere, Category = "Input|Contexts")
	TObjectPtr<UInputMappingContext> DialogMappingContext;

	UPROPERTY(EditAnywhere, Category = "Input|Contexts")
	TObjectPtr<UInputMappingContext> MenuMappingContext;

	/** Right stick aim, 2D axis */
	UPROPERTY(EditAnywhere, Category = "Input|Gameplay")
	TObjectPtr<UInputAction> AimStickAction;

	/** Q / E and bumpers, 1D axis, negative rotates left */
	UPROPERTY(EditAnywhere, Category = "Input|Gameplay")
	TObjectPtr<UInputAction> CameraRotateAction;

	/** Middle mouse button held */
	UPROPERTY(EditAnywhere, Category = "Input|Gameplay")
	TObjectPtr<UInputAction> CameraDragAction;

	/** Horizontal mouse delta, used while dragging */
	UPROPERTY(EditAnywhere, Category = "Input|Gameplay")
	TObjectPtr<UInputAction> CameraDragDeltaAction;

	/** Wheel and D-pad up / down, 1D axis in wheel notches, + zooms in */
	UPROPERTY(EditAnywhere, Category = "Input|Gameplay")
	TObjectPtr<UInputAction> ZoomAction;

	UPROPERTY(EditAnywhere, Category = "Input|Gameplay")
	TObjectPtr<UInputAction> BackpackAction;

	UPROPERTY(EditAnywhere, Category = "Input|Gameplay")
	TObjectPtr<UInputAction> MapAction;

	UPROPERTY(EditAnywhere, Category = "Input|Gameplay")
	TObjectPtr<UInputAction> JournalAction;

	UPROPERTY(EditAnywhere, Category = "Input|Gameplay")
	TObjectPtr<UInputAction> PauseAction;

	UPROPERTY(EditAnywhere, Category = "Input|Dialog")
	TObjectPtr<UInputAction> DialogAdvanceAction;

	UPROPERTY(EditAnywhere, Category = "Input|Dialog")
	TObjectPtr<UInputAction> DialogNavigateAction;

	UPROPERTY(EditAnywhere, Category = "Input|Menu")
	TObjectPtr<UInputAction> MenuNavigateAction;

	UPROPERTY(EditAnywhere, Category = "Input|Menu")
	TObjectPtr<UInputAction> MenuConfirmAction;

	UPROPERTY(EditAnywhere, Category = "Input|Menu")
	TObjectPtr<UInputAction> MenuBackAction;

	UPROPERTY(EditAnywhere, Category = "Input|Menu")
	TObjectPtr<UInputAction> MenuPrevTabAction;

	UPROPERTY(EditAnywhere, Category = "Input|Menu")
	TObjectPtr<UInputAction> MenuNextTabAction;

	/** Stepped rotation: angle of one step */
	UPROPERTY(EditAnywhere, Category = "Camera",
		meta = (ClampMin = 1, ClampMax = 180, Units = "Degrees"))
	float RotationStep = 45.f;

	/** Free rotation: speed while Q / E or a bumper is held */
	UPROPERTY(EditAnywhere, Category = "Camera",
		meta = (ClampMin = 0, Units = "DegreesPerSecond"))
	float FreeRotationSpeed = 120.f;

	/**
	 *  Degrees per unit of horizontal mouse delta while dragging. Mouse X
	 *  is pixels times the 0.07 sensitivity from DefaultInput.ini.
	 */
	UPROPERTY(EditAnywhere, Category = "Camera", meta = (ClampMin = 0))
	float DragSensitivity = 3.f;

	/** How fast the camera yaw catches up with its target */
	UPROPERTY(EditAnywhere, Category = "Camera", meta = (ClampMin = 0))
	float RotationInterpSpeed = 10.f;

	UPROPERTY(EditAnywhere, Category = "Camera",
		meta = (ClampMin = 0, Units = "cm"))
	float MinArmLength = 900.f;

	UPROPERTY(EditAnywhere, Category = "Camera",
		meta = (ClampMin = 0, Units = "cm"))
	float MaxArmLength = 2400.f;

	/** Arm length change per zoom notch */
	UPROPERTY(EditAnywhere, Category = "Camera",
		meta = (ClampMin = 0, Units = "cm"))
	float ZoomStep = 150.f;

	/** How fast the arm length catches up with its target */
	UPROPERTY(EditAnywhere, Category = "Camera", meta = (ClampMin = 0))
	float ZoomInterpSpeed = 8.f;

	/** Right stick deflection needed to aim with it */
	UPROPERTY(EditAnywhere, Category = "Aim",
		meta = (ClampMin = 0, ClampMax = 1))
	float StickAimThreshold = 0.3f;

	/** Distance of the stick aim point from her */
	UPROPERTY(EditAnywhere, Category = "Aim",
		meta = (ClampMin = 0, Units = "cm"))
	float StickAimDistance = 600.f;

	/** Gamepad analog deflection that counts as using the gamepad */
	UPROPERTY(EditAnywhere, Category = "Input",
		meta = (ClampMin = 0, ClampMax = 1))
	float GamepadAnalogThreshold = 0.3f;

	EAcrpgInputContext InputContext = EAcrpgInputContext::Gameplay;
	EAcrpgInputDevice LastInputDevice = EAcrpgInputDevice::KeyboardMouse;

	float CameraYaw = 0.f;
	float TargetCameraYaw = 0.f;
	float TargetArmLength = 0.f;
	bool bDraggingCamera = false;
	FVector2D StickAim = FVector2D::ZeroVector;

public:

	/** Fires when the player switches between keyboard and gamepad */
	UPROPERTY(BlueprintAssignable, Category = "Input")
	FInputDeviceChangedSignature OnInputDeviceChanged;

	AProtagonistController();

	virtual void PlayerTick(float DeltaTime) override;

	virtual bool InputKey(const FInputKeyEventArgs& Params) override;

	/** Activates one mapping context and removes the others */
	UFUNCTION(BlueprintCallable, Category = "Input")
	void SetInputContext(EAcrpgInputContext Context);

	UFUNCTION(BlueprintPure, Category = "Input")
	EAcrpgInputContext GetInputContext() const { return InputContext; }

	UFUNCTION(BlueprintPure, Category = "Input")
	EAcrpgInputDevice GetLastInputDevice() const { return LastInputDevice; }

	/** Console: switches between stepped and free camera rotation */
	UFUNCTION(Exec, BlueprintCallable, Category = "Camera")
	void SetFreeCameraRotation(bool bFree);

protected:

	virtual void SetupInputComponent() override;

	virtual void OnPossess(APawn* InPawn) override;

	bool IsFreeRotation() const;

	void SetLastInputDevice(EAcrpgInputDevice Device);

	/** Points her at the cursor or along the right stick */
	void UpdateAim(AProtagonistCharacter* Protagonist);

	void UpdateCamera(AProtagonistCharacter* Protagonist, float DeltaTime);

	void CameraRotateStarted(const FInputActionValue& Value);
	void CameraRotateTriggered(const FInputActionValue& Value);
	void CameraDragStarted();
	void CameraDragCompleted();
	void CameraDragDelta(const FInputActionValue& Value);
	void Zoom(const FInputActionValue& Value);
	void AimStick(const FInputActionValue& Value);
	void AimStickCompleted();

	/** Placeholder for actions that later issues implement */
	void LogPendingAction(const FInputActionInstance& Instance);
};
