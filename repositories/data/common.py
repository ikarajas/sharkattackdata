class FullyResolvedAttackStatus:
    Found, NotFound, FoundInDifferentLocation = range(3)

class FullyResolvedAttackResponse:
    """
    Response DTO for AttackRepository.getFullyResolvedAttack()
    """
    def __init__(self, status, countryId, areaId, attack):
        self.status = status
        self.countryId = countryId
        self.areaId = areaId
        self.attack = attack
