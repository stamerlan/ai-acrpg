#include "SneakSubsystem.h"
#include "Components/SpotLightComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Engine/World.h"
#include "EngineUtils.h"
#include "HAL/IConsoleManager.h"
#include "acrpg.h"

namespace
{
	const FName DarknessTag(TEXT("Darkness"));
	const FName LitZoneTag(TEXT("LitZone"));
	const FName SightLightTag(TEXT("SightLight"));
	const FName HearNoiseName(TEXT("HearNoise"));

	/** Lit zones count from the ground up to this height above them */
	constexpr float LitZoneHeight = 400.f;

	/**
	 *  The zone radius: the largest horizontal extent of its meshes (the
	 *  Lit marker's disc; labels and poles are smaller)
	 */
	float ZoneRadius(const AActor* Zone)
	{
		float Radius = 0.f;
		TInlineComponentArray<UStaticMeshComponent*> Meshes(Zone);
		for (const UStaticMeshComponent* Mesh : Meshes)
		{
			if (Mesh->GetStaticMesh())
			{
				const FVector Extent = Mesh->Bounds.BoxExtent;
				Radius = FMath::Max(Radius,
					static_cast<float>(FMath::Max(Extent.X, Extent.Y)));
			}
		}
		return Radius;
	}

	FAutoConsoleCommandWithWorldArgsAndOutputDevice SneakInfoCommand(
		TEXT("Sneak.Info"),
		TEXT("Shows the lit zones, light cones and darkness"),
		FConsoleCommandWithWorldArgsAndOutputDeviceDelegate::CreateLambda(
			[](const TArray<FString>& Args, UWorld* World,
				FOutputDevice& Ar)
			{
				if (const USneakSubsystem* Sneak =
					World ? World->GetSubsystem<USneakSubsystem>() : nullptr)
				{
					Ar.Log(Sneak->Describe());
				}
			}));
}

void USneakSubsystem::Refresh() const
{
	if (CachedFrame == GFrameCounter)
	{
		return;
	}
	CachedFrame = GFrameCounter;
	bCachedDark = false;
	CachedZones.Reset();
	CachedLights.Reset();
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		AActor* Actor = *It;
		if (Actor->ActorHasTag(DarknessTag))
		{
			bCachedDark = true;
		}
		if (Actor->ActorHasTag(LitZoneTag))
		{
			CachedZones.Add(Actor);
		}
		const bool bActorTagged = Actor->ActorHasTag(SightLightTag);
		TInlineComponentArray<USpotLightComponent*> Spots(Actor);
		for (USpotLightComponent* Spot : Spots)
		{
			if (bActorTagged || Spot->ComponentHasTag(SightLightTag))
			{
				CachedLights.Add(Spot);
			}
		}
	}
}

bool USneakSubsystem::IsDark() const
{
	Refresh();
	return bCachedDark;
}

bool USneakSubsystem::IsLit(FVector Location, AActor* Ignore) const
{
	Refresh();
	if (!bCachedDark)
	{
		return true;
	}
	for (const TWeakObjectPtr<AActor>& Zone : CachedZones)
	{
		if (!Zone.IsValid())
		{
			continue;
		}
		const float Radius = ZoneRadius(Zone.Get());
		const FVector Base = Zone->GetActorLocation();
		if (FVector::Dist2D(Base, Location) <= Radius
			&& Location.Z >= Base.Z - 50.f
			&& Location.Z <= Base.Z + LitZoneHeight)
		{
			return true;
		}
	}
	for (const TWeakObjectPtr<USpotLightComponent>& Light : CachedLights)
	{
		if (Light.IsValid() && IsInLightCone(Light.Get(), Location, Ignore))
		{
			return true;
		}
	}
	return false;
}

bool USneakSubsystem::IsInLightCone(const USpotLightComponent* Light,
	FVector Location, AActor* Ignore) const
{
	if (!Light || !Light->IsVisible() || Light->Intensity <= 0.f)
	{
		return false;
	}
	const FVector From = Light->GetComponentLocation();
	const FVector ToPoint = Location - From;
	const float Distance = ToPoint.Size();
	if (Distance > Light->AttenuationRadius || Distance < KINDA_SMALL_NUMBER)
	{
		return false;
	}
	const float CosAngle = FVector::DotProduct(ToPoint / Distance,
		Light->GetForwardVector());
	if (CosAngle < FMath::Cos(FMath::DegreesToRadians(Light->OuterConeAngle)))
	{
		return false;
	}
	FCollisionQueryParams Params(SCENE_QUERY_STAT(SneakLightCone), false);
	Params.AddIgnoredActor(Light->GetOwner());
	if (Ignore)
	{
		Params.AddIgnoredActor(Ignore);
	}
	FHitResult Hit;
	return !GetWorld()->LineTraceSingleByChannel(Hit, From, Location,
		ECC_Visibility, Params);
}

void USneakSubsystem::ReportNoise(FVector Location, float Radius, FName Tag)
{
	UE_LOG(Logacrpg, Log, TEXT("Noise %s at %s, radius %.0f"),
		*Tag.ToString(), *Location.ToCompactString(), Radius);
	TArray<AActor*> Listeners;
	for (TActorIterator<AActor> It(GetWorld()); It; ++It)
	{
		if (FVector::Dist(It->GetActorLocation(), Location) <= Radius
			&& It->FindFunction(HearNoiseName))
		{
			Listeners.Add(*It);
		}
	}
	for (AActor* Listener : Listeners)
	{
		UFunction* Func = Listener->FindFunction(HearNoiseName);
		uint8* Params = static_cast<uint8*>(
			FMemory_Alloca(FMath::Max<int32>(Func->ParmsSize, 1)));
		FMemory::Memzero(Params, Func->ParmsSize);
		for (TFieldIterator<FProperty> It(Func);
			It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			It->InitializeValue_InContainer(Params);
			if (const FStructProperty* Vec = CastField<FStructProperty>(*It))
			{
				if (Vec->Struct == TBaseStructure<FVector>::Get())
				{
					*Vec->ContainerPtrToValuePtr<FVector>(Params) = Location;
				}
			}
			else if (const FNameProperty* Name = CastField<FNameProperty>(*It))
			{
				*Name->ContainerPtrToValuePtr<FName>(Params) = Tag;
			}
		}
		Listener->ProcessEvent(Func, Params);
		for (TFieldIterator<FProperty> It(Func);
			It && It->HasAnyPropertyFlags(CPF_Parm); ++It)
		{
			It->DestroyValue_InContainer(Params);
		}
	}
}

FString USneakSubsystem::Describe() const
{
	Refresh();
	FString Out = FString::Printf(TEXT("Dark: %s\nLit zones (%d):"),
		bCachedDark ? TEXT("yes") : TEXT("no"), CachedZones.Num());
	for (const TWeakObjectPtr<AActor>& Zone : CachedZones)
	{
		if (Zone.IsValid())
		{
			Out += FString::Printf(TEXT("\n  %s at %s, radius %.0f"),
				*Zone->GetActorNameOrLabel(),
				*Zone->GetActorLocation().ToCompactString(),
				ZoneRadius(Zone.Get()));
		}
	}
	Out += FString::Printf(TEXT("\nLight cones (%d):"), CachedLights.Num());
	for (const TWeakObjectPtr<USpotLightComponent>& Light : CachedLights)
	{
		if (Light.IsValid())
		{
			Out += FString::Printf(TEXT("\n  %s.%s %s, %.0f cm, %.0f deg"),
				*Light->GetOwner()->GetActorNameOrLabel(),
				*Light->GetName(),
				Light->IsVisible() ? TEXT("on") : TEXT("off"),
				Light->AttenuationRadius, Light->OuterConeAngle);
		}
	}
	return Out;
}
