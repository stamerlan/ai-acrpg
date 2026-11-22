#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "ChickenCharacter.generated.h"

class UCameraComponent;
class USpringArmComponent;
class UCameraOcclusionComponent;
class UInputAction;
struct FInputActionValue;
struct FInputActionInstance;

/**
 *  The Ambitious Chicken. Moves relative to the camera yaw (the control
 *  rotation set by AChickenPlayerController) and faces the aim point while
 *  one is set, otherwise her movement direction.
 */
UCLASS(abstract)
class AChickenCharacter : public ACharacter
{
	GENERATED_BODY()

	/** Isometric-style camera boom, yaw follows the control rotation */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components",
		meta = (AllowPrivateAccess = "true"))
	TObjectPtr<USpringArmComponent> CameraBoom;

	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components",
		meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UCameraComponent> Camera;

	/** Fades out walls, roofs and props between the camera and her */
	UPROPERTY(VisibleAnywhere, BlueprintReadOnly, Category = "Components",
		meta = (AllowPrivateAccess = "true"))
	TObjectPtr<UCameraOcclusionComponent> CameraOcclusion;

protected:

	UPROPERTY(EditAnywhere, Category = "Input")
	TObjectPtr<UInputAction> MoveAction;

	UPROPERTY(EditAnywhere, Category = "Input")
	TObjectPtr<UInputAction> FireAction;

	UPROPERTY(EditAnywhere, Category = "Input")
	TObjectPtr<UInputAction> PeckAction;

	UPROPERTY(EditAnywhere, Category = "Input")
	TObjectPtr<UInputAction> FlutterAction;

	UPROPERTY(EditAnywhere, Category = "Input")
	TObjectPtr<UInputAction> ReloadAction;

	UPROPERTY(EditAnywhere, Category = "Input")
	TObjectPtr<UInputAction> EatCornAction;

	/** How fast she turns toward the aim point */
	UPROPERTY(EditAnywhere, Category = "Aim",
		meta = (ClampMin = 0, Units = "DegreesPerSecond"))
	float AimTurnRate = 1440.f;

	/** True while an aim point is set */
	bool bHasAimPoint = false;

	/** World location she is aiming at */
	FVector AimPoint = FVector::ZeroVector;

public:

	AChickenCharacter();

	virtual void Tick(float DeltaSeconds) override;

	virtual void SetupPlayerInputComponent(
		UInputComponent* PlayerInputComponent) override;

	/** Makes her face and aim at a world location */
	UFUNCTION(BlueprintCallable, Category = "Aim")
	void SetAimPoint(const FVector& Point);

	/** Stops aiming, she faces her movement direction again */
	UFUNCTION(BlueprintCallable, Category = "Aim")
	void ClearAimPoint();

	UFUNCTION(BlueprintPure, Category = "Aim")
	bool HasAimPoint() const { return bHasAimPoint; }

	UFUNCTION(BlueprintPure, Category = "Aim")
	FVector GetAimPoint() const { return AimPoint; }

	USpringArmComponent* GetCameraBoom() const { return CameraBoom; }

	UCameraComponent* GetCamera() const { return Camera; }

protected:

	void Move(const FInputActionValue& Value);

	/** Placeholder for actions that later issues implement */
	void LogPendingAction(const FInputActionInstance& Instance);
};
