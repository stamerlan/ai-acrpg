#include "ChickenPlayerController.h"
#include "AcrpgGameUserSettings.h"
#include "ChickenCharacter.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Camera/CameraComponent.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputKeyEventArgs.h"
#include "InputMappingContext.h"
#include "acrpg.h"

AChickenPlayerController::AChickenPlayerController()
{
	bShowMouseCursor = true;
	DefaultMouseCursor = EMouseCursor::Crosshairs;
}

void AChickenPlayerController::SetupInputComponent()
{
	Super::SetupInputComponent();

	if (!IsLocalPlayerController())
	{
		return;
	}
	SetInputContext(EAcrpgInputContext::Gameplay);

	UEnhancedInputComponent* Input =
		Cast<UEnhancedInputComponent>(InputComponent);
	if (!Input)
	{
		UE_LOG(Logacrpg, Error,
			TEXT("'%s' needs an Enhanced Input Component"),
			*GetNameSafe(this));
		return;
	}

	Input->BindAction(AimStickAction, ETriggerEvent::Triggered, this,
		&AChickenPlayerController::AimStick);
	Input->BindAction(AimStickAction, ETriggerEvent::Completed, this,
		&AChickenPlayerController::AimStickCompleted);
	Input->BindAction(CameraRotateAction, ETriggerEvent::Started, this,
		&AChickenPlayerController::CameraRotateStarted);
	Input->BindAction(CameraRotateAction, ETriggerEvent::Triggered, this,
		&AChickenPlayerController::CameraRotateTriggered);
	Input->BindAction(CameraDragAction, ETriggerEvent::Started, this,
		&AChickenPlayerController::CameraDragStarted);
	Input->BindAction(CameraDragAction, ETriggerEvent::Completed, this,
		&AChickenPlayerController::CameraDragCompleted);
	Input->BindAction(CameraDragDeltaAction, ETriggerEvent::Triggered, this,
		&AChickenPlayerController::CameraDragDelta);
	Input->BindAction(ZoomAction, ETriggerEvent::Triggered, this,
		&AChickenPlayerController::Zoom);

	for (UInputAction* Action : {BackpackAction.Get(), MapAction.Get(),
		JournalAction.Get(), PauseAction.Get(), MenuNavigateAction.Get(),
		MenuConfirmAction.Get(), MenuBackAction.Get(),
		MenuPrevTabAction.Get(), MenuNextTabAction.Get()})
	{
		Input->BindAction(Action, ETriggerEvent::Started, this,
			&AChickenPlayerController::LogPendingAction);
	}
}

void AChickenPlayerController::OnPossess(APawn* InPawn)
{
	Super::OnPossess(InPawn);

	// The player start yaw sets the initial camera direction
	TargetCameraYaw = InPawn->GetActorRotation().Yaw;
	if (!IsFreeRotation())
	{
		TargetCameraYaw =
			FMath::GridSnap(TargetCameraYaw, RotationStep);
	}
	CameraYaw = TargetCameraYaw;
	SetControlRotation(FRotator(0.f, CameraYaw, 0.f));

	if (const AChickenCharacter* Chicken = Cast<AChickenCharacter>(InPawn))
	{
		TargetArmLength = FMath::Clamp(
			Chicken->GetCameraBoom()->TargetArmLength,
			MinArmLength, MaxArmLength);
		PlayerArmLength = TargetArmLength;
	}
	bCameraFocus = false;
	FocusAlpha = 0.f;
}

void AChickenPlayerController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);

	AChickenCharacter* Chicken = Cast<AChickenCharacter>(GetPawn());
	if (!Chicken)
	{
		return;
	}

	if (InputContext == EAcrpgInputContext::Gameplay)
	{
		UpdateAim(Chicken);
	}
	else
	{
		Chicken->ClearAimPoint();
	}
	UpdateCamera(Chicken, DeltaTime);
}

bool AChickenPlayerController::InputKey(const FInputKeyEventArgs& Params)
{
	// Analog keys send events while at rest, so they need a real deflection
	const bool bAnalog = Params.Key.IsAnalog();
	if (Params.Key.IsGamepadKey())
	{
		if (!bAnalog ||
			FMath::Abs(Params.AmountDepressed) > GamepadAnalogThreshold)
		{
			SetLastInputDevice(EAcrpgInputDevice::Gamepad);
		}
	}
	else if (!Params.bIsTouchEvent &&
		(!bAnalog || !FMath::IsNearlyZero(Params.AmountDepressed)))
	{
		SetLastInputDevice(EAcrpgInputDevice::KeyboardMouse);
	}

	// Windows sends a second click within its double-click time (500 ms)
	// as a double click. Enhanced Input loses one whose press and release
	// land in the same frame (only plain presses get the sub-tick tap
	// fix), so the game takes every click as a plain press.
	if (Params.Event == IE_DoubleClick)
	{
		FInputKeyEventArgs Press = Params;
		Press.Event = IE_Pressed;
		return Super::InputKey(Press);
	}
	return Super::InputKey(Params);
}

void AChickenPlayerController::SetInputContext(EAcrpgInputContext Context)
{
	UEnhancedInputLocalPlayerSubsystem* Subsystem =
		ULocalPlayer::GetSubsystem<UEnhancedInputLocalPlayerSubsystem>(
			GetLocalPlayer());
	if (!Subsystem)
	{
		return;
	}

	InputContext = Context;
	for (const UInputMappingContext* Mapping : {GameplayMappingContext.Get(),
		DialogMappingContext.Get(), MenuMappingContext.Get()})
	{
		if (Mapping)
		{
			Subsystem->RemoveMappingContext(Mapping);
		}
	}

	const UInputMappingContext* Active =
		Context == EAcrpgInputContext::Gameplay ? GameplayMappingContext :
		Context == EAcrpgInputContext::Dialog ? DialogMappingContext :
		MenuMappingContext;
	if (Active)
	{
		Subsystem->AddMappingContext(Active, 0);
	}

	StickAim = FVector2D::ZeroVector;
	bDraggingCamera = false;
	CurrentMouseCursor = Context == EAcrpgInputContext::Gameplay
		? EMouseCursor::Crosshairs : EMouseCursor::Default;
}

void AChickenPlayerController::SetFreeCameraRotation(bool bFree)
{
	if (UAcrpgGameUserSettings* Settings =
		UAcrpgGameUserSettings::GetAcrpgGameUserSettings())
	{
		Settings->CameraRotationStyle = bFree
			? ECameraRotationStyle::Free : ECameraRotationStyle::Stepped;
		Settings->SaveSettings();
	}

	if (!bFree)
	{
		TargetCameraYaw = FMath::GridSnap(TargetCameraYaw, RotationStep);
	}
}

bool AChickenPlayerController::IsFreeRotation() const
{
	const UAcrpgGameUserSettings* Settings =
		UAcrpgGameUserSettings::GetAcrpgGameUserSettings();
	return Settings &&
		Settings->CameraRotationStyle == ECameraRotationStyle::Free;
}

void AChickenPlayerController::SetLastInputDevice(EAcrpgInputDevice Device)
{
	if (Device == LastInputDevice)
	{
		return;
	}

	LastInputDevice = Device;
	SetShowMouseCursor(Device == EAcrpgInputDevice::KeyboardMouse);
	OnInputDeviceChanged.Broadcast(Device);
}

void AChickenPlayerController::UpdateAim(AChickenCharacter* Chicken)
{
	if (LastInputDevice == EAcrpgInputDevice::Gamepad)
	{
		if (StickAim.Size() < StickAimThreshold)
		{
			Chicken->ClearAimPoint();
			return;
		}

		// Stick X is right, Y is forward, relative to the camera yaw
		const FVector Direction = FRotator(0.f, CameraYaw, 0.f)
			.RotateVector(FVector(StickAim.Y, StickAim.X, 0.f))
			.GetSafeNormal();
		Chicken->SetAimPoint(
			Chicken->GetActorLocation() + Direction * StickAimDistance);
		return;
	}

	// Project the cursor onto the ground plane under her feet. Off the
	// viewport the last aim point stays.
	FVector Origin;
	FVector Direction;
	if (!DeprojectMousePositionToWorld(Origin, Direction) ||
		Direction.Z > -UE_KINDA_SMALL_NUMBER)
	{
		return;
	}
	const double GroundZ = Chicken->GetNavAgentLocation().Z;
	Chicken->SetAimPoint(
		Origin + Direction * ((GroundZ - Origin.Z) / Direction.Z));
}

void AChickenPlayerController::UpdateCamera(
	AChickenCharacter* Chicken, float DeltaTime)
{
	TargetCameraYaw = FRotator::NormalizeAxis(TargetCameraYaw);
	const float Delta =
		FMath::FindDeltaAngleDegrees(CameraYaw, TargetCameraYaw);
	const float Alpha = FMath::Min(1.f, DeltaTime * RotationInterpSpeed);
	CameraYaw = FMath::IsNearlyZero(Delta, 0.01f)
		? TargetCameraYaw
		: FRotator::NormalizeAxis(CameraYaw + Delta * Alpha);
	SetControlRotation(FRotator(0.f, CameraYaw, 0.f));

	// The focus blends over the player's own zoom, which comes back as it
	// was once the focus ends
	PlayerArmLength = FMath::FInterpTo(PlayerArmLength, TargetArmLength,
		DeltaTime, ZoomInterpSpeed);
	FocusAlpha = FMath::FInterpConstantTo(FocusAlpha, bCameraFocus ? 1.f : 0.f,
		DeltaTime, 1.f / (bCameraFocus ? FocusInTime : FocusBlendOutTime));
	const float Focus = FMath::SmoothStep(0.f, 1.f, FocusAlpha);

	USpringArmComponent* Boom = Chicken->GetCameraBoom();
	Boom->TargetArmLength = FMath::Lerp(PlayerArmLength,
		FMath::Min(FocusArmLength, PlayerArmLength), Focus);
	Boom->SocketOffset.Y = FocusSideOffset * Focus;

	// Motion blur smears the whole frame while the focus moves the camera
	// (worst on the snap out after a hit, when she must see the threat)
	FPostProcessSettings& Post = Chicken->GetCamera()->PostProcessSettings;
	Post.bOverride_MotionBlurAmount = FocusAlpha > 0.f && FocusAlpha < 1.f;
	Post.MotionBlurAmount = 0.f;
}

void AChickenPlayerController::SetCameraFocus(bool bFocus, bool bSnapOut)
{
	bCameraFocus = bFocus;
	FocusBlendOutTime = bSnapOut ? FocusSnapOutTime : FocusOutTime;
}

void AChickenPlayerController::CameraRotateStarted(
	const FInputActionValue& Value)
{
	if (!IsFreeRotation())
	{
		const float Sign = FMath::Sign(Value.Get<float>());
		TargetCameraYaw = FMath::GridSnap(
			TargetCameraYaw + Sign * RotationStep, RotationStep);
	}
}

void AChickenPlayerController::CameraRotateTriggered(
	const FInputActionValue& Value)
{
	if (IsFreeRotation())
	{
		TargetCameraYaw += Value.Get<float>() * FreeRotationSpeed *
			GetWorld()->GetDeltaSeconds();
	}
}

void AChickenPlayerController::CameraDragStarted()
{
	bDraggingCamera = true;
}

void AChickenPlayerController::CameraDragCompleted()
{
	bDraggingCamera = false;
	if (!IsFreeRotation())
	{
		TargetCameraYaw = FMath::GridSnap(TargetCameraYaw, RotationStep);
	}
}

void AChickenPlayerController::CameraDragDelta(const FInputActionValue& Value)
{
	if (bDraggingCamera)
	{
		TargetCameraYaw += Value.Get<float>() * DragSensitivity;
	}
}

void AChickenPlayerController::Zoom(const FInputActionValue& Value)
{
	if (bCameraFocus)
	{
		return;
	}
	TargetArmLength = FMath::Clamp(
		TargetArmLength - Value.Get<float>() * ZoomStep,
		MinArmLength, MaxArmLength);
}

void AChickenPlayerController::AimStick(const FInputActionValue& Value)
{
	StickAim = Value.Get<FVector2D>();
}

void AChickenPlayerController::AimStickCompleted()
{
	StickAim = FVector2D::ZeroVector;
}

void AChickenPlayerController::LogPendingAction(
	const FInputActionInstance& Instance)
{
	UE_LOG(Logacrpg, Log, TEXT("%s: not implemented yet"),
		*GetNameSafe(Instance.GetSourceAction()));
}
