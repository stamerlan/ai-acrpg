#include "ProtagonistCharacter.h"
#include "CameraOcclusionComponent.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "EnhancedInputComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/SpringArmComponent.h"
#include "InputAction.h"
#include "acrpg.h"

AProtagonistCharacter::AProtagonistCharacter()
{
	PrimaryActorTick.bCanEverTick = true;

	GetCapsuleComponent()->InitCapsuleSize(42.f, 96.f);

	bUseControllerRotationPitch = false;
	bUseControllerRotationYaw = false;
	bUseControllerRotationRoll = false;

	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->MaxWalkSpeed = 500.f;
	Movement->MaxAcceleration = 3000.f;
	Movement->BrakingDecelerationWalking = 3000.f;
	Movement->bOrientRotationToMovement = true;
	Movement->RotationRate = FRotator(0.f, 720.f, 0.f);
	Movement->bCanWalkOffLedges = true;

	// Yaw comes from the control rotation, pitch stays at the iso angle
	CameraBoom = CreateDefaultSubobject<USpringArmComponent>(
		TEXT("CameraBoom"));
	CameraBoom->SetupAttachment(RootComponent);
	CameraBoom->SetRelativeRotation(FRotator(-50.f, 0.f, 0.f));
	CameraBoom->TargetArmLength = 1600.f;
	CameraBoom->bUsePawnControlRotation = true;
	CameraBoom->bInheritPitch = false;
	CameraBoom->bInheritRoll = false;
	CameraBoom->bInheritYaw = true;
	CameraBoom->bDoCollisionTest = false;
	CameraBoom->bEnableCameraLag = true;
	CameraBoom->CameraLagSpeed = 12.f;

	Camera = CreateDefaultSubobject<UCameraComponent>(TEXT("Camera"));
	Camera->SetupAttachment(CameraBoom, USpringArmComponent::SocketName);
	Camera->bUsePawnControlRotation = false;
	Camera->SetFieldOfView(55.f);

	CameraOcclusion = CreateDefaultSubobject<UCameraOcclusionComponent>(
		TEXT("CameraOcclusion"));
}

void AProtagonistCharacter::Tick(float DeltaSeconds)
{
	Super::Tick(DeltaSeconds);

	UCharacterMovementComponent* Movement = GetCharacterMovement();
	Movement->bOrientRotationToMovement = !bHasAimPoint;
	if (!bHasAimPoint)
	{
		return;
	}

	const FVector ToAim = AimPoint - GetActorLocation();
	if (ToAim.SizeSquared2D() < FMath::Square(10.f))
	{
		return;
	}

	const FRotator Current = GetActorRotation();
	const FRotator Target(0.f, ToAim.Rotation().Yaw, 0.f);
	SetActorRotation(FMath::RInterpConstantTo(
		Current, Target, DeltaSeconds, AimTurnRate));
}

void AProtagonistCharacter::SetupPlayerInputComponent(
	UInputComponent* PlayerInputComponent)
{
	Super::SetupPlayerInputComponent(PlayerInputComponent);

	UEnhancedInputComponent* Input =
		Cast<UEnhancedInputComponent>(PlayerInputComponent);
	if (!Input)
	{
		UE_LOG(Logacrpg, Error,
			TEXT("'%s' needs an Enhanced Input Component"),
			*GetNameSafe(this));
		return;
	}

	Input->BindAction(MoveAction, ETriggerEvent::Triggered, this,
		&AProtagonistCharacter::Move);

	for (UInputAction* Action : {FireAction.Get(), PeckAction.Get(),
		FlutterAction.Get(), ReloadAction.Get(), EatCornAction.Get()})
	{
		Input->BindAction(Action, ETriggerEvent::Started, this,
			&AProtagonistCharacter::LogPendingAction);
	}
}

void AProtagonistCharacter::SetAimPoint(const FVector& Point)
{
	AimPoint = Point;
	bHasAimPoint = true;
}

void AProtagonistCharacter::ClearAimPoint()
{
	bHasAimPoint = false;
}

void AProtagonistCharacter::Move(const FInputActionValue& Value)
{
	// X is right, Y is forward, both relative to the camera yaw
	const FVector2D Input = Value.Get<FVector2D>();
	const FRotator Yaw(0.f, GetControlRotation().Yaw, 0.f);
	AddMovementInput(Yaw.RotateVector(FVector::ForwardVector), Input.Y);
	AddMovementInput(Yaw.RotateVector(FVector::RightVector), Input.X);
}

void AProtagonistCharacter::LogPendingAction(
	const FInputActionInstance& Instance)
{
	UE_LOG(Logacrpg, Log, TEXT("%s: not implemented yet"),
		*GetNameSafe(Instance.GetSourceAction()));
}
