#include "ProtagonistController.h"
#include "AcrpgGameUserSettings.h"
#include "ProtagonistCharacter.h"
#include "EnhancedInputComponent.h"
#include "EnhancedInputSubsystems.h"
#include "Engine/LocalPlayer.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "InputKeyEventArgs.h"
#include "InputMappingContext.h"
#include "acrpg.h"

AProtagonistController::AProtagonistController()
{
	bShowMouseCursor = true;
	DefaultMouseCursor = EMouseCursor::Crosshairs;
}

void AProtagonistController::SetupInputComponent()
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
		&AProtagonistController::AimStick);
	Input->BindAction(AimStickAction, ETriggerEvent::Completed, this,
		&AProtagonistController::AimStickCompleted);
	Input->BindAction(CameraRotateAction, ETriggerEvent::Started, this,
		&AProtagonistController::CameraRotateStarted);
	Input->BindAction(CameraRotateAction, ETriggerEvent::Triggered, this,
		&AProtagonistController::CameraRotateTriggered);
	Input->BindAction(CameraDragAction, ETriggerEvent::Started, this,
		&AProtagonistController::CameraDragStarted);
	Input->BindAction(CameraDragAction, ETriggerEvent::Completed, this,
		&AProtagonistController::CameraDragCompleted);
	Input->BindAction(CameraDragDeltaAction, ETriggerEvent::Triggered, this,
		&AProtagonistController::CameraDragDelta);
	Input->BindAction(ZoomAction, ETriggerEvent::Triggered, this,
		&AProtagonistController::Zoom);

	for (UInputAction* Action : {BackpackAction.Get(), MapAction.Get(),
		JournalAction.Get(), PauseAction.Get(), DialogAdvanceAction.Get(),
		DialogNavigateAction.Get(), MenuNavigateAction.Get(),
		MenuConfirmAction.Get(), MenuBackAction.Get(),
		MenuPrevTabAction.Get(), MenuNextTabAction.Get()})
	{
		Input->BindAction(Action, ETriggerEvent::Started, this,
			&AProtagonistController::LogPendingAction);
	}
}

void AProtagonistController::OnPossess(APawn* InPawn)
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

	if (const AProtagonistCharacter* Protagonist =
		Cast<AProtagonistCharacter>(InPawn))
	{
		TargetArmLength = FMath::Clamp(
			Protagonist->GetCameraBoom()->TargetArmLength,
			MinArmLength, MaxArmLength);
	}
}

void AProtagonistController::PlayerTick(float DeltaTime)
{
	Super::PlayerTick(DeltaTime);

	AProtagonistCharacter* Protagonist =
		Cast<AProtagonistCharacter>(GetPawn());
	if (!Protagonist)
	{
		return;
	}

	if (InputContext == EAcrpgInputContext::Gameplay)
	{
		UpdateAim(Protagonist);
	}
	else
	{
		Protagonist->ClearAimPoint();
	}
	UpdateCamera(Protagonist, DeltaTime);
}

bool AProtagonistController::InputKey(const FInputKeyEventArgs& Params)
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

	return Super::InputKey(Params);
}

void AProtagonistController::SetInputContext(EAcrpgInputContext Context)
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

void AProtagonistController::SetFreeCameraRotation(bool bFree)
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

bool AProtagonistController::IsFreeRotation() const
{
	const UAcrpgGameUserSettings* Settings =
		UAcrpgGameUserSettings::GetAcrpgGameUserSettings();
	return Settings &&
		Settings->CameraRotationStyle == ECameraRotationStyle::Free;
}

void AProtagonistController::SetLastInputDevice(EAcrpgInputDevice Device)
{
	if (Device == LastInputDevice)
	{
		return;
	}

	LastInputDevice = Device;
	SetShowMouseCursor(Device == EAcrpgInputDevice::KeyboardMouse);
	OnInputDeviceChanged.Broadcast(Device);
}

void AProtagonistController::UpdateAim(AProtagonistCharacter* Protagonist)
{
	if (LastInputDevice == EAcrpgInputDevice::Gamepad)
	{
		if (StickAim.Size() < StickAimThreshold)
		{
			Protagonist->ClearAimPoint();
			return;
		}

		// Stick X is right, Y is forward, relative to the camera yaw
		const FVector Direction = FRotator(0.f, CameraYaw, 0.f)
			.RotateVector(FVector(StickAim.Y, StickAim.X, 0.f))
			.GetSafeNormal();
		Protagonist->SetAimPoint(
			Protagonist->GetActorLocation() + Direction * StickAimDistance);
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
	const double GroundZ = Protagonist->GetNavAgentLocation().Z;
	Protagonist->SetAimPoint(
		Origin + Direction * ((GroundZ - Origin.Z) / Direction.Z));
}

void AProtagonistController::UpdateCamera(
	AProtagonistCharacter* Protagonist, float DeltaTime)
{
	TargetCameraYaw = FRotator::NormalizeAxis(TargetCameraYaw);
	const float Delta =
		FMath::FindDeltaAngleDegrees(CameraYaw, TargetCameraYaw);
	const float Alpha = FMath::Min(1.f, DeltaTime * RotationInterpSpeed);
	CameraYaw = FMath::IsNearlyZero(Delta, 0.01f)
		? TargetCameraYaw
		: FRotator::NormalizeAxis(CameraYaw + Delta * Alpha);
	SetControlRotation(FRotator(0.f, CameraYaw, 0.f));

	USpringArmComponent* Boom = Protagonist->GetCameraBoom();
	Boom->TargetArmLength = FMath::FInterpTo(Boom->TargetArmLength,
		TargetArmLength, DeltaTime, ZoomInterpSpeed);
}

void AProtagonistController::CameraRotateStarted(
	const FInputActionValue& Value)
{
	if (!IsFreeRotation())
	{
		const float Sign = FMath::Sign(Value.Get<float>());
		TargetCameraYaw = FMath::GridSnap(
			TargetCameraYaw + Sign * RotationStep, RotationStep);
	}
}

void AProtagonistController::CameraRotateTriggered(
	const FInputActionValue& Value)
{
	if (IsFreeRotation())
	{
		TargetCameraYaw += Value.Get<float>() * FreeRotationSpeed *
			GetWorld()->GetDeltaSeconds();
	}
}

void AProtagonistController::CameraDragStarted()
{
	bDraggingCamera = true;
}

void AProtagonistController::CameraDragCompleted()
{
	bDraggingCamera = false;
	if (!IsFreeRotation())
	{
		TargetCameraYaw = FMath::GridSnap(TargetCameraYaw, RotationStep);
	}
}

void AProtagonistController::CameraDragDelta(const FInputActionValue& Value)
{
	if (bDraggingCamera)
	{
		TargetCameraYaw += Value.Get<float>() * DragSensitivity;
	}
}

void AProtagonistController::Zoom(const FInputActionValue& Value)
{
	TargetArmLength = FMath::Clamp(
		TargetArmLength - Value.Get<float>() * ZoomStep,
		MinArmLength, MaxArmLength);
}

void AProtagonistController::AimStick(const FInputActionValue& Value)
{
	StickAim = Value.Get<FVector2D>();
}

void AProtagonistController::AimStickCompleted()
{
	StickAim = FVector2D::ZeroVector;
}

void AProtagonistController::LogPendingAction(
	const FInputActionInstance& Instance)
{
	UE_LOG(Logacrpg, Log, TEXT("%s: not implemented yet"),
		*GetNameSafe(Instance.GetSourceAction()));
}
