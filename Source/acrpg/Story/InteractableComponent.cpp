#include "InteractableComponent.h"
#include "Engine/CollisionProfile.h"

UInteractableComponent::UInteractableComponent()
{
	Prompt = NSLOCTEXT("Interaction", "Talk", "Talk");
	InitSphereRadius(200.f);
	SetCollisionProfileName(UCollisionProfile::CustomCollisionProfileName);
	SetCollisionEnabled(ECollisionEnabled::QueryOnly);
	SetCollisionObjectType(ECC_WorldDynamic);
	SetCollisionResponseToAllChannels(ECR_Ignore);
	SetCollisionResponseToChannel(ECC_Pawn, ECR_Overlap);
	SetGenerateOverlapEvents(true);
	SetCanEverAffectNavigation(false);
	SetHiddenInGame(true);
	ShapeColor = FColor::Cyan;
}
