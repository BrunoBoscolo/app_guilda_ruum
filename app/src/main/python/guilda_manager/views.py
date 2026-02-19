from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
from rest_framework import viewsets, status, decorators
from rest_framework.response import Response
from django.templatetags.static import static
from .models import Guild, Quest, Member, Monster, Squad, Dispatch, SquadRank, Building, Map, Hexagon, Pin
from .forms import MonsterForm
from .serializers import GuildDashboardSerializer, BuildConstructionSerializer, QuestSerializer, MemberSerializer
import hashlib
import random
from types import SimpleNamespace

class GuildViewSet(viewsets.ModelViewSet):
    queryset = Guild.objects.all()
    serializer_class = GuildDashboardSerializer

    @decorators.action(detail=True, methods=['post'])
    def construct_building(self, request, pk=None):
        """
        Handles the purchase of a building.
        Expects 'building_slug' in the request data.
        """
        guild = self.get_object()
        serializer = BuildConstructionSerializer(data=request.data, context={'guild': guild})

        if serializer.is_valid():
            serializer.save()
            # Return the updated guild dashboard
            guild.refresh_from_db()
            dashboard_serializer = self.get_serializer(guild)
            return Response(dashboard_serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class QuestViewSet(viewsets.ModelViewSet):
    queryset = Quest.objects.all()
    serializer_class = QuestSerializer

    @decorators.action(detail=True, methods=['post'])
    def delegate(self, request, pk=None):
        quest = self.get_object()

        # Check if already delegated or completed
        if quest.status not in [Quest.Status.OPEN, Quest.Status.IN_PROGRESS]:
             return Response({"error": "Quest cannot be delegated in its current status."}, status=status.HTTP_400_BAD_REQUEST)

        member_ids = request.data.get('assigned_members', [])
        if not member_ids:
            return Response({"error": "No members assigned."}, status=status.HTTP_400_BAD_REQUEST)

        # Verify members exist and belong to the guild
        # Filter by guild to ensure they belong to the same guild as the quest
        members = Member.objects.filter(id__in=member_ids, guild=quest.guild)

        # Note: We don't strict check len(members) == len(member_ids) because duplications or invalid IDs might be passed.
        # But for safety, we should ensure at least one valid member.
        if not members.exists():
             return Response({"error": "Invalid members provided."}, status=status.HTTP_400_BAD_REQUEST)

        # Assign members
        quest.assigned_members.set(members)
        quest.status = Quest.Status.DELEGATED
        quest.save()

        # Resolve logic
        result = quest.resolve_delegation()

        # Serialize updated quest
        serializer = self.get_serializer(quest)
        return Response({
            "quest": serializer.data,
            "delegation_result": result
        }, status=status.HTTP_200_OK)

    @decorators.action(detail=True, methods=['patch'])
    def complete(self, request, pk=None):
        quest = self.get_object()

        if quest.status == Quest.Status.COMPLETED:
             return Response({"error": "Quest already completed."}, status=status.HTTP_400_BAD_REQUEST)

        quest.complete_quest()

        serializer = self.get_serializer(quest)
        return Response(serializer.data, status=status.HTTP_200_OK)

def root_routing_view(request):
    if Guild.objects.exists():
        return redirect('sede')
    else:
        return redirect('entry_portal')

def entry_portal_view(request):
    if Guild.objects.exists():
        return redirect('sede')
    return render(request, 'guilda_manager/entry_portal.html')

def create_guild_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        emblem = request.POST.get('emblem')
        legal_status = request.POST.get('legal_status')
        moral_alignment = request.POST.get('moral_alignment')
        motto = request.POST.get('motto')

        if name:
            Guild.objects.create(
                name=name,
                emblem=emblem or 'swords',
                legal_status=legal_status or Guild.LegalStatus.INDEPENDENT,
                moral_alignment=moral_alignment or Guild.MoralAlignment.HUMANITARIAN,
                description=motto or ''
            )
            return redirect('sede')

    return render(request, 'guilda_manager/create_guild.html')

def sync_guild_view(request):
    if request.method == 'POST':
        code = request.POST.get('code')
        # Simulate Sync Logic
        # In a real app, this would fetch from server.
        # Here we just validate and create a dummy guild or assume it worked.
        # Check code format XXX-0000
        import re
        if code and re.match(r'^[A-Z]{3}-\d{4}$', code):
             # Create a guild with this code if not exists
             if not Guild.objects.exists():
                 Guild.objects.create(
                     name=f"Guilda {code}",
                     code=code,
                     description="Guilda sincronizada via código."
                 )
             return redirect('sede')
        else:
            return render(request, 'guilda_manager/sync_guild.html', {'error': 'Código inválido'})

    return render(request, 'guilda_manager/sync_guild.html')

def share_guild_view(request):
    guild = Guild.objects.first()
    if not guild:
        return redirect('entry_portal')
    return render(request, 'guilda_manager/share_guild.html', {'guild': guild})

def landing_view(request):
    return render(request, 'guilda_manager/landing.html')

def sede_view(request):
    guild = Guild.objects.first()
    if not guild:
        return redirect('entry_portal')

    max_xp = 100  # Placeholder as per design
    xp_percent = min((guild.gxp / max_xp) * 100, 100)

    members_count = guild.members.count()
    members_max = guild.max_member_slots
    members_percent = min((members_count / members_max) * 100, 100) if members_max > 0 else 0

    constructions_count = guild.guild_buildings.count()
    constructions_max = guild.base_stats['base_building_slots']
    constructions_percent = min((constructions_count / constructions_max) * 100, 100) if constructions_max > 0 else 0

    treasury_percent = min((guild.funds / guild.max_gold_cap) * 100, 100) if guild.max_gold_cap > 0 else 0

    context = {
        'guild': guild,
        'max_xp': max_xp,
        'xp_percent': xp_percent,
        'members_count': members_count,
        'members_max': members_max,
        'members_percent': members_percent,
        'constructions_count': constructions_count,
        'constructions_max': constructions_max,
        'constructions_percent': constructions_percent,
        'treasury_percent': treasury_percent,
    }

    return render(request, 'guilda_manager/sede.html', context)

def missoes_view(request):
    guild = Guild.objects.first()
    if not guild:
        return redirect('entry_portal')

    quests = Quest.objects.all()

    for quest in quests:
        # Create a deterministic seed based on quest ID and title
        seed_str = f"{quest.id}-{quest.title}"
        seed_hash = hashlib.md5(seed_str.encode('utf-8')).hexdigest()
        seed_int = int(seed_hash, 16)

        rng = random.Random(seed_int)

        # Rotation: Random between -20 and 20 degrees
        quest.seal_rotation = rng.randint(-20, 20)

        # Position offsets: Random between -10 and 10 pixels
        quest.seal_top_offset = rng.randint(-10, 10)
        quest.seal_right_offset = rng.randint(-10, 10)

        # Seal Image Path
        quest.seal_image_path = f"guilda_manager/images/SELOS/{quest.rank}.png"

    return render(request, 'guilda_manager/missoes.html', {'quests': quests, 'guild': guild})

def construcoes_view(request):
    return render(request, 'guilda_manager/construcoes_hub.html')

def construcoes_projetos_view(request):
    guild = Guild.objects.first()
    if not guild:
         return redirect('entry_portal')

    # Get IDs of buildings already constructed
    built_ids = guild.guild_buildings.values_list('building_id', flat=True)

    # Available buildings are those NOT built
    buildings = Building.objects.exclude(id__in=built_ids).order_by('cost')

    context = {
        'guild': guild,
        'buildings': buildings,
        'in_progress_buildings': [] # Placeholder
    }
    return render(request, 'guilda_manager/construcoes_projetos.html', context)

def construcoes_infra_view(request):
    guild = Guild.objects.first()
    if not guild:
         return redirect('entry_portal')

    constructions = guild.guild_buildings.select_related('building').all().order_by('-built_at')

    context = {
        'guild': guild,
        'constructions': constructions
    }
    return render(request, 'guilda_manager/construcoes_infra.html', context)

def bestiario_hub_view(request):
    return render(request, 'guilda_manager/bestiario_hub.html')

def bestiario_rememoracao_view(request):
    monsters = Monster.objects.all().order_by('name')
    context = {'monsters': monsters}

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'save':
            monster_id = request.POST.get('monster_id')
            monster = get_object_or_404(Monster, id=monster_id)
            form = MonsterForm(request.POST, instance=monster)

            # Dice Pool Logic Validation
            dice_pool_str = request.POST.get('dice_pool_str', '')
            if dice_pool_str:
                dice_pool = [int(x) for x in dice_pool_str.split(',') if x]
            else:
                dice_pool = []

            dice_pool.sort(reverse=True) # Highest dice first (6, 6, 4, 1...)

            if form.is_valid():
                # --- Validation Logic ---
                changed_fields = form.changed_data

                # Field Level Mapping
                level_1_fields = ['name', 'size', 'monster_type', 'description', 'challenge_level']
                level_2_fields = ['combat_role', 'defense', 'movement', 'habitat']
                level_3_fields = ['health_points', 'weaknesses', 'immunities', 'special_abilities']

                validation_error = None

                # Check each changed field
                temp_pool = list(dice_pool)

                # Sort changes by level required (Highest first) to use best dice optimally
                # Or rather, check if we have A die that can satisfy.
                # Since a 6 can satisfy L1, L2, or L3, we should try to satisfy L3 changes first with 5-6s.

                changes_by_level = []
                for field in changed_fields:
                    if field in level_3_fields:
                        changes_by_level.append(3)
                    elif field in level_2_fields:
                        changes_by_level.append(2)
                    else:
                        changes_by_level.append(1)

                changes_by_level.sort(reverse=True) # Check L3 requirements first

                for req_level in changes_by_level:
                    # Find a die in pool that satisfies req_level
                    # L3 needs 5-6, L2 needs 3-6, L1 needs 1-6
                    found_die_index = -1

                    min_die_value = 1
                    if req_level == 3: min_die_value = 5
                    elif req_level == 2: min_die_value = 3

                    # Look for smallest die that satisfies the condition to save big dice for big reqs?
                    # Actually, since we process highest reqs first, we should just take the first valid die?
                    # No, if we have [6, 4] and need L3 and L2.
                    # L3 needs 6. Left [4]. L2 needs 3+. 4 works.
                    # If we have [6, 6] and need L1 and L1. Both work.
                    # Strategy: Use the smallest die that satisfies the requirement to preserve high dice?
                    # But we are iterating Requirements High to Low.
                    # L3 Requirement: Needs 5+.
                    # L2 Requirement: Needs 3+.
                    # If we have [5, 4]. L3 takes 5. L2 takes 4. OK.
                    # If we have [6, 5]. L3 takes 5 (save 6?). No, L3 takes 6 or 5.

                    # Let's just find ANY die that works. Since we sorted requirements Descending,
                    # we must satisfy the hardest ones first.
                    # We should prioritize using the "weakest" die that still works for the current requirement?
                    # Example: Pool [6, 5, 2]. Reqs: L3, L1.
                    # L3 needs 5+. Dice options: 6, 5.
                    # If we use 6: Pool [5, 2]. L1 needs 1+. 2 works. OK.
                    # If we use 5: Pool [6, 2]. L1 needs 1+. 2 works. OK.

                    # Example: Pool [6, 4]. Reqs: L2, L2.
                    # L2 needs 3+. Dice options: 6, 4.
                    # If we use 4: Pool [6]. Next L2 needs 3+. 6 works. OK.
                    # If we use 6: Pool [4]. Next L2 needs 3+. 4 works. OK.

                    # It seems greedy approach (taking first available) usually works if we sort requirements.
                    # But let's be safe: Find the *smallest* die that satisfies the condition.
                    # This saves larger dice for potential harder requirements (though we process harder first).
                    # Actually, since we process hardest first, we can just take *any* valid die.
                    # Because if a die works for L3, it works for L2/L1.
                    # But a die that works for L2 might NOT work for L3.
                    # So for an L3 req, we MUST use a 5-6.
                    # For an L2 req, we MUST use a 3-6.

                    best_die_idx = -1

                    # Search for a die >= min_die_value
                    # Since we want to save higher dice for higher reqs (which we process first),
                    # We should just take the first one we find?
                    # Wait, we process L3 first. We consume a 5 or 6.
                    # Then we process L2. We consume a 3, 4, 5, or 6.
                    # If we have [6, 3] and reqs [L3, L2].
                    # L3 takes 6. Rem: [3]. L2 takes 3. OK.
                    # If we have [6, 6] and reqs [L3, L2].
                    # L3 takes 6. Rem: [6]. L2 takes 6. OK.

                    # Greedy match is fine because the set of dice that satisfy L3 is a subset of L2.

                    for i, die in enumerate(temp_pool):
                        if die >= min_die_value:
                            found_die_index = i
                            # Optimization: Use the smallest valid die?
                            # e.g. Pool [6, 5]. Req L3. Both work.
                            # e.g. Pool [6, 4]. Req L2. Both work.
                            # It doesn't strictly matter for correctness if we process constraints from strict to loose.
                            break

                    if found_die_index != -1:
                        temp_pool.pop(found_die_index)
                    else:
                        validation_error = f"Você não possui dados de memória suficientes para alterar o campo (Nível {req_level}). Dados disponíveis: {dice_pool}"
                        break

                if validation_error:
                    context['error_message'] = validation_error
                    context['form'] = form
                    context['selected_monster'] = monster # Keep context
                    context['dice_pool'] = dice_pool # Return dice to context
                    context['dice_pool_str'] = dice_pool_str
                else:
                    form.save()
                    context['success_message'] = f"Memórias sobre {monster.name} salvas com sucesso! ({len(changed_fields)} campos alterados)"
                    context['selected_monster'] = monster
            else:
                context['error_message'] = "Erro ao salvar o formulário. Verifique os campos."
                context['form'] = form

        elif action == 'roll':
            monster_id = request.POST.get('monster_id')
            is_immediate = request.POST.get('is_immediate') == 'on'
            use_tonic = request.POST.get('use_tonic') == 'on'

            # Default values
            d20_roll = None
            tonic_rolls = [] # For display
            dc = 15
            bonus = 0
            total_check = 0
            margin = 0
            is_crit = False
            auto_rolled = False
            result_type = "Teste Padrão"

            # Determine Dice Pool Size
            if is_immediate:
                pool_size = 5
                result_type = "Imediato (Sem Teste)"
            else:
                # Decay Logic
                try:
                    dc = int(request.POST.get('dc', 15))
                except (ValueError, TypeError):
                    dc = 15

                try:
                    bonus = int(request.POST.get('bonus') or 0)
                except (ValueError, TypeError):
                    bonus = 0

                d20_roll_raw = request.POST.get('d20_roll')

                if not d20_roll_raw:
                    if use_tonic:
                        r1 = random.randint(1, 20)
                        r2 = random.randint(1, 20)
                        d20_roll = max(r1, r2)
                        tonic_rolls = [r1, r2]
                    else:
                        d20_roll = random.randint(1, 20)
                    auto_rolled = True
                else:
                    try:
                        d20_roll = int(d20_roll_raw)
                    except (ValueError, TypeError):
                        d20_roll = random.randint(1, 20)
                    auto_rolled = False

                total_check = d20_roll + bonus
                margin = total_check - dc
                is_crit = (d20_roll == 20)

                if is_crit:
                    pool_size = 6
                    result_type = "Sucesso Crítico"
                elif margin >= 0:
                    pool_size = 4
                    result_type = "Sucesso"
                elif margin >= -4:
                    pool_size = 3
                    result_type = "Falha"
                else:
                    pool_size = 1
                    result_type = "Falha Grave"

            # Roll Memory Dice
            dice_pool = [random.randint(1, 6) for _ in range(pool_size)]
            dice_pool.sort(reverse=True)

            # Analyze Dice
            vague_dice = [d for d in dice_pool if 1 <= d <= 2]
            tactical_dice = [d for d in dice_pool if 3 <= d <= 4]
            vital_dice = [d for d in dice_pool if 5 <= d <= 6]

            selected_monster = None
            form = None
            if monster_id:
                selected_monster = get_object_or_404(Monster, id=monster_id)
                form = MonsterForm(instance=selected_monster)

            dice_pool_str = ",".join(map(str, dice_pool))
            context.update({
                'selected_monster': selected_monster,
                'form': form,
                'd20_roll': d20_roll,
                'tonic_rolls': tonic_rolls,
                'bonus': bonus,
                'dc': dc,
                'total_check': total_check,
                'margin': margin,
                'is_crit': is_crit,
                'result_type': result_type,
                'dice_pool': dice_pool,
                'dice_pool_str': dice_pool_str,
                'vague_count': len(vague_dice),
                'tactical_count': len(tactical_dice),
                'vital_count': len(vital_dice),
                'auto_rolled': auto_rolled,
                'has_result': True,
                'is_immediate': is_immediate,
            })

    return render(request, 'guilda_manager/bestiario_rememoracao.html', context)

def bestiario_list_view(request):
    monsters = Monster.objects.all().order_by('name')

    # Filters
    search_query = request.GET.get('search', '')
    type_filter = request.GET.get('type', '')

    if search_query:
        monsters = monsters.filter(name__icontains=search_query)

    if type_filter:
        monsters = monsters.filter(monster_type=type_filter)

    # Overview Stats
    total_monsters = monsters.count()

    # Aggregations
    from django.db.models import Count, Avg, Max

    stats = monsters.aggregate(avg_nd=Avg('challenge_level'), max_nd=Max('challenge_level'))
    avg_nd = stats['avg_nd']
    max_nd = stats['max_nd']

    # Find most common type
    most_common_type_data = monsters.exclude(monster_type='').values('monster_type').annotate(count=Count('monster_type')).order_by('-count').first()
    most_common_type = most_common_type_data['monster_type'] if most_common_type_data else "Nenhum"

    # Get all unique types for the filter dropdown
    all_types = Monster.objects.values_list('monster_type', flat=True).distinct().order_by('monster_type')
    # Filter out empty strings if any
    all_types = [t for t in all_types if t]

    context = {
        'monsters': monsters,
        'search_query': search_query,
        'type_filter': type_filter,
        'total_monsters': total_monsters,
        'most_common_type': most_common_type,
        'avg_nd': avg_nd,
        'max_nd': max_nd,
        'all_types': all_types,
    }

    return render(request, 'guilda_manager/bestiario_list.html', context)

def bestiario_edit_view(request, slug):
    monster = get_object_or_404(Monster, slug=slug)

    if request.method == 'POST':
        form = MonsterForm(request.POST, instance=monster)
        if form.is_valid():
            form.save()
            return redirect('bestiario_list')
    else:
        form = MonsterForm(instance=monster)

    return render(request, 'guilda_manager/bestiario_edit.html', {'form': form, 'monster': monster})

def bestiario_create_view(request):
    if request.method == 'POST':
        form = MonsterForm(request.POST)
        if form.is_valid():
            monster = form.save(commit=False)
            monster.slug = slugify(monster.name)

            # Handle duplicate slugs
            original_slug = monster.slug
            counter = 1
            while Monster.objects.filter(slug=monster.slug).exists():
                monster.slug = f"{original_slug}-{counter}"
                counter += 1

            monster.save()
            return redirect('bestiario_list')
    else:
        form = MonsterForm()

    # Dummy monster for template compatibility
    dummy_monster = SimpleNamespace(register_level=1, name="Nova Criatura")

    return render(request, 'guilda_manager/bestiario_edit.html', {'form': form, 'monster': dummy_monster})

def mestre_view(request):
    guild = Guild.objects.first() # Assuming single guild
    if not guild:
        return redirect('entry_portal')

    context = {}

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'dispatch':
            try:
                npc_count = int(request.POST.get('npc_count', 0))
                duration = int(request.POST.get('duration', 1))
            except ValueError:
                npc_count = 0
                duration = 1

            mission_id = request.POST.get('mission_id')

            active_members_count = guild.members.filter(status=Member.Status.ACTIVE).count()

            if npc_count <= 0:
                 context['error_message'] = "Número de NPCs inválido."
            elif npc_count > active_members_count:
                 context['error_message'] = f"Número de NPCs excede o total de membros ativos ({active_members_count})."
            elif not mission_id:
                 context['error_message'] = "Missão não selecionada."
            else:
                mission = get_object_or_404(Quest, id=mission_id)

                Dispatch.objects.create(
                    mission=mission,
                    npc_count=npc_count,
                    duration_days=duration,
                    status=Dispatch.Status.PENDING,
                    rank=mission.rank
                )

                mission.status = Quest.Status.DELEGATED
                mission.save()

                context['success_message'] = f"Despacho iniciado para missão '{mission.title}' com {npc_count} NPCs!"

        elif action == 'resolve':
            dispatch_id = request.POST.get('dispatch_id')
            dispatch = get_object_or_404(Dispatch, id=dispatch_id)

            outcome = dispatch.resolve()

            if outcome:
                msg = f"Resultado: Rolagem {outcome['roll']}."
                if outcome['deaths'] > 0:
                    msg += f" {outcome['deaths']} Baixas: {', '.join(outcome['dead_names'])}."
                else:
                    msg += " Sucesso!"
                context['success_message'] = msg
            else:
                context['error_message'] = "Não foi possível resolver o despacho (status inválido)."

        elif action == 'create_quick_mission':
            # Quick Mission Templates
            templates = [
                {"title": "Escolta de Caravana", "desc": "Proteger uma caravana de mercadores viajando por estradas perigosas."},
                {"title": "Caça aos Goblins", "desc": "Um grupo de goblins está saqueando fazendas próximas. Elimine-os."},
                {"title": "Entrega Urgente", "desc": "Entregar uma mensagem sigilosa para um nobre em uma cidade vizinha."},
                {"title": "Investigação na Floresta", "desc": "Lenhadores relataram sons estranhos e luzes na floresta sombria."},
                {"title": "Limpeza de Porão", "desc": "Ratos gigantes invadiram o porão da taverna local."},
            ]
            template = random.choice(templates)

            # Random Rank (weighted towards lower ranks)
            rank = random.choices(['F', 'E', 'D'], weights=[50, 30, 20], k=1)[0]

            # Calculate Rewards based on Rank
            gxp = Quest.RANK_GXP_REWARDS.get(rank, 5)
            gold = gxp * 10  # Simple formula: 1 GXP = 10 Gold
            duration = random.randint(1, 3)  # 1-3 days for quick missions

            Quest.objects.create(
                title=template['title'],
                description=template['desc'],
                rank=rank,
                gxp_reward=gxp,
                gold_reward=gold,
                duration_days=duration,
                guild=guild,
                type=Quest.Type.EXTERNAL,
                status=Quest.Status.OPEN
            )
            context['success_message'] = f"Missão Rápida '{template['title']}' criada com sucesso!"

        elif action == 'create_custom_mission':
            title = request.POST.get('title')
            description = request.POST.get('description')
            rank = request.POST.get('rank')
            duration_raw = request.POST.get('duration')
            gold_raw = request.POST.get('reward_gold', 0)
            gxp_raw = request.POST.get('reward_xp', 0)

            valid_numbers = True
            try:
                gold = float(gold_raw)
                gxp = int(gxp_raw)
                duration = int(duration_raw)
            except (ValueError, TypeError):
                valid_numbers = False
                context['error_message'] = "Valores numéricos inválidos."

            if valid_numbers and title and description:
                Quest.objects.create(
                    title=title,
                    description=description,
                    rank=rank,
                    gxp_reward=gxp,
                    gold_reward=gold,
                    duration_days=duration,
                    guild=guild,
                    type=Quest.Type.EXTERNAL,
                    status=Quest.Status.OPEN
                )
                context['success_message'] = f"Missão Personalizada '{title}' criada com sucesso!"
            else:
                if not context.get('error_message'):
                     context['error_message'] = "Título e descrição são obrigatórios."

                context['form_data'] = {
                    'title': title,
                    'description': description,
                    'rank': rank,
                    'duration': duration_raw,
                    'reward_gold': gold_raw,
                    'reward_xp': gxp_raw
                }
                context['force_tab'] = 'contratos'
                context['force_mission_view'] = 'custom'

        elif action == 'config':
            guild.legal_status = request.POST.get('legal_status')
            guild.moral_alignment = request.POST.get('moral_alignment')
            guild.save()
            context['success_message'] = "Configurações da Guilda atualizadas."

        elif action == 'manage_gold':
            try:
                amount = float(request.POST.get('amount', 0))
                operation = request.POST.get('operation')

                if amount < 0:
                     context['error_message'] = "O valor deve ser positivo."
                else:
                    if operation == 'add':
                        current_funds = guild.funds
                        max_cap = guild.max_gold_cap

                        if current_funds >= max_cap:
                             context['error_message'] = "O tesouro já está cheio!"
                        else:
                            new_funds = current_funds + Decimal(amount)
                            if new_funds > max_cap:
                                guild.funds = max_cap
                                context['success_message'] = f"Tesouro adicionado. (Limitado ao teto de {max_cap} T$)"
                            else:
                                guild.funds = new_funds
                                context['success_message'] = f"{amount} T$ adicionados ao tesouro."
                            guild.save()

                    elif operation == 'remove':
                        current_funds = guild.funds
                        new_funds = current_funds - Decimal(amount)

                        if new_funds < 0:
                            guild.funds = 0
                            context['success_message'] = "Tesouro removido. (Fundos zerados)"
                        else:
                            guild.funds = new_funds
                            context['success_message'] = f"{amount} T$ removidos do tesouro."
                        guild.save()

            except ValueError:
                context['error_message'] = "Valor inválido."

        elif action == 'delete_guild':
            guild.delete()
            return redirect('entry_portal')

        # --- Squad CRUD ---
        elif action == 'create_squad':
            name = request.POST.get('name')
            if name:
                # Assign lowest rank by default
                initial_rank = SquadRank.objects.order_by('order').first()
                Squad.objects.create(name=name, guild=guild, rank=initial_rank)
                context['success_message'] = f"Esquadrão {name} criado."

        elif action == 'delete_squad':
            squad_id = request.POST.get('squad_id')
            Squad.objects.filter(id=squad_id).delete()
            context['success_message'] = "Esquadrão removido."

        elif action == 'edit_squad':
            squad_id = request.POST.get('squad_id')
            name = request.POST.get('name')
            rank_id = request.POST.get('rank_id')
            squad = get_object_or_404(Squad, id=squad_id)
            if name: squad.name = name
            if rank_id: squad.rank_id = rank_id
            squad.save()
            context['success_message'] = f"Esquadrão {squad.name} atualizado."

        # --- Rank CRUD ---
        elif action == 'create_rank':
            name = request.POST.get('name')
            order = request.POST.get('order')
            missions = request.POST.get('missions')
            guild_level = request.POST.get('guild_level')

            if name and order:
                SquadRank.objects.create(
                    name=name,
                    order=order,
                    missions_required=missions or 0,
                    min_guild_level=guild_level or 1
                )
                context['success_message'] = f"Patente {name} criada."

        elif action == 'delete_rank':
            rank_id = request.POST.get('rank_id')
            try:
                SquadRank.objects.filter(id=rank_id).delete()
                context['success_message'] = "Patente removida."
            except Exception as e:
                context['error_message'] = "Não foi possível remover a patente (pode estar em uso)."

        elif action == 'edit_rank':
            rank_id = request.POST.get('rank_id')
            rank_obj = get_object_or_404(SquadRank, id=rank_id)
            rank_obj.name = request.POST.get('name')
            rank_obj.order = request.POST.get('order')
            rank_obj.missions_required = request.POST.get('missions')
            rank_obj.min_guild_level = request.POST.get('guild_level')
            rank_obj.save()
            context['success_message'] = f"Patente {rank_obj.name} atualizada."

        elif action == 'update_hex':
            try:
                q = int(request.POST.get('q'))
                r = int(request.POST.get('r'))
                title = request.POST.get('title')
                description = request.POST.get('description')
                pin_id = request.POST.get('pin_id')

                # Ensure map exists
                game_map = Map.objects.first()
                if not game_map:
                    # Create default if missing (should be handled by setup script but safety first)
                    game_map = Map.objects.create(name="Reino", background_image="guilda_manager/placeholder.png")

                hex_obj, created = Hexagon.objects.get_or_create(
                    map=game_map,
                    q=q,
                    r=r
                )

                hex_obj.title = title
                hex_obj.description = description

                if pin_id:
                    hex_obj.pin = Pin.objects.get(id=pin_id)
                else:
                    hex_obj.pin = None

                hex_obj.save()
                context['success_message'] = f"Hexágono ({q}, {r}) atualizado com sucesso."
                context['force_tab'] = 'mapa'

            except (ValueError, Pin.DoesNotExist):
                context['error_message'] = "Erro ao atualizar hexágono. Dados inválidos."

        elif action == 'upload_map':
            if 'map_image' in request.FILES:
                image_file = request.FILES['map_image']

                game_map = Map.objects.first()
                if not game_map:
                    game_map = Map(name="Reino")

                game_map.background_image = image_file
                game_map.save()
                context['success_message'] = "Imagem do mapa atualizada com sucesso!"
                context['force_tab'] = 'mapa'
            else:
                context['error_message'] = "Nenhuma imagem selecionada."

    # Data for Template
    squads = Squad.objects.all().order_by('-rank__order', 'name')
    squad_ranks = SquadRank.objects.all().order_by('order')
    dispatches = Dispatch.objects.filter(status=Dispatch.Status.PENDING).order_by('target_date')
    open_quests = Quest.objects.filter(status=Quest.Status.OPEN).order_by('rank', 'title')

    # History Stats
    # Quest counts by rank
    from django.db.models import Count
    quest_counts = Quest.objects.filter(status=Quest.Status.COMPLETED).values('rank').annotate(count=Count('rank')).order_by('rank')
    # Convert to dict for easier template access
    quest_stats = {item['rank']: item['count'] for item in quest_counts}

    # Ensure all ranks exist in dict
    for r in Quest.Rank.values:
        if r not in quest_stats:
            quest_stats[r] = 0

    # Map Data for Mestre View
    game_map = Map.objects.first()
    map_hexes = []
    map_image_url = static('guilda_manager/placeholder.png')

    # Need full hex details for editing
    if game_map:
        if game_map.background_image and game_map.background_image.name != 'guilda_manager/placeholder.png':
             map_image_url = game_map.background_image.url

        hexes = Hexagon.objects.filter(map=game_map).select_related('pin')
        for h in hexes:
            map_hexes.append({
                'q': h.q,
                'r': h.r,
                'title': h.title,
                'description': h.description,
                'pin_id': h.pin.id if h.pin else None,
                'pin_name': h.pin.name if h.pin else None
            })

    pins = Pin.objects.all().order_by('name')

    context.update({
        'guild': guild,
        'pins': pins,
        'squads': squads,
        'squad_ranks': squad_ranks,
        'dispatches': dispatches,
        'open_quests': open_quests,
        'quest_stats': quest_stats,
        'ranks': Quest.Rank.choices,
        'legal_statuses': Guild.LegalStatus.choices,
        'moral_alignments': Guild.MoralAlignment.choices,
        'now': timezone.now(),
        'game_map': game_map,
        'map_hexes': map_hexes,
        'map_image_url': map_image_url
    })

    return render(request, 'guilda_manager/mestre.html', context)


def mapa_view(request):
    game_map = Map.objects.first()
    locations = []
    map_image_url = static('guilda_manager/placeholder.png')

    if game_map:
        if game_map.background_image:
             map_image_url = game_map.background_image.url

        hexes = Hexagon.objects.filter(map=game_map).select_related('pin')
        for h in hexes:
            loc = {
                'q': h.q,
                'r': h.r,
                'title': h.title,
                'description': h.description,
            }
            if h.pin:
                loc['model'] = h.pin.glb_path
            locations.append(loc)

    context = {'locations': locations, 'map_image_url': map_image_url}
    if game_map:
        context['map'] = game_map

    return render(request, 'guilda_manager/mapa.html', context)
