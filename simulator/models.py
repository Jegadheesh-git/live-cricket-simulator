from django.db import models

class Nationality(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=3) # e.g. IND, AUS

    def __str__(self):
        return self.name

class Team(models.Model):
    name = models.CharField(max_length=100)
    short_name = models.CharField(max_length=10, unique=True)
    logo_url = models.URLField(blank=True, null=True)
    
    def __str__(self):
        return self.short_name

class Player(models.Model):
    ROLE_CHOICES = (
        ('BATSMAN', 'Batsman'),
        ('BOWLER', 'Bowler'),
        ('ALL_ROUNDER', 'All Rounder'),
        ('WICKET_KEEPER', 'Wicket Keeper'),
    )
    BATTING_HAND_CHOICES = (
        ('RIGHT', 'Right Hand'),
        ('LEFT', 'Left Hand'),
        ('UNKNOWN', 'Unknown'),
    )
    BOWLING_HAND_CHOICES = (
        ('RIGHT', 'Right Hand'),
        ('LEFT', 'Left Hand'),
        ('UNKNOWN', 'Unknown'),
    )
    BOWLING_STYLE_CHOICES = (
        ('FAST', 'Fast'),
        ('SPIN', 'Spin'),
        ('MEDIUM', 'Medium'),
    )
    GENDER_CHOICES = (
        ('M', 'Male'),
        ('F', 'Female'),
    )

    first_name = models.CharField(max_length=100)
    middle_name = models.CharField(max_length=100, blank=True, null=True)
    last_name = models.CharField(max_length=100)
    nick_name = models.CharField(max_length=100, blank=True, null=True)
    
    nationality = models.ForeignKey(Nationality, on_delete=models.SET_NULL, null=True, blank=True)
    dob = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='M')
    
    height = models.FloatField(help_text="Height in cm", null=True, blank=True)
    weight = models.FloatField(help_text="Weight in kg", null=True, blank=True)
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    batting_hand = models.CharField(max_length=20, choices=BATTING_HAND_CHOICES, default='RIGHT')
    bowling_hand = models.CharField(max_length=20, choices=BOWLING_HAND_CHOICES, default='RIGHT')
    bowling_style = models.CharField(max_length=20, choices=BOWLING_STYLE_CHOICES, blank=True, null=True)
    
    batting_style = models.CharField(max_length=100, help_text="Technical attributes", blank=True, null=True)
    fielding_skill = models.CharField(max_length=100, blank=True, null=True)
    wicket_keeping_skill = models.CharField(max_length=100, blank=True, null=True)
    
    height_type = models.CharField(max_length=20, help_text="Short/Medium/Tall", blank=True, null=True)
    bowling_type = models.CharField(max_length=50, help_text="Pace/Spin variations", blank=True, null=True)
    batting_type = models.CharField(max_length=50, help_text="Technical attributes", blank=True, null=True)
    
    def __str__(self):
        return f"{self.first_name} {self.last_name}"

class Match(models.Model):
    MATCH_TYPE_CHOICES = (
        ('T20', 'T20'),
        ('ODI', 'ODI'),
        ('TEST', 'Test'),
    )
    TOSS_DECISION_CHOICES = (
        ('BAT', 'Bat'),
        ('BOWL', 'Bowl'),
    )
    
    teams = models.ManyToManyField(Team, related_name='matches')
    date = models.DateTimeField()
    venue = models.CharField(max_length=255, blank=True, null=True)
    match_type = models.CharField(max_length=10, choices=MATCH_TYPE_CHOICES, default='T20')
    is_live = models.BooleanField(default=False)
    match_ended = models.BooleanField(default=False)
    seconds_per_ball = models.FloatField(default=1.0)
    
    # Toss & Status
    toss_won_by = models.ForeignKey(Team, on_delete=models.SET_NULL, null=True, blank=True, related_name='toss_wins')
    opt_to = models.CharField(max_length=10, choices=TOSS_DECISION_CHOICES, null=True, blank=True)
    current_innings = models.IntegerField(default=1)
    
    def __str__(self):
        return f"Match {self.id} | {self.match_type} | {self.date}"

class PlayingSquad(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='squads')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    is_captain = models.BooleanField(default=False)
    is_wicket_keeper = models.BooleanField(default=False)

    class Meta:
        unique_together = ('match', 'player')

    def __str__(self):
        return f"{self.player} ({self.team}) - Match {self.match_id}"

# --- Phase 3 Core Models ---

class InningsScore(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='innings_scores')
    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    innings = models.IntegerField()
    
    total_runs = models.IntegerField(default=0)
    total_wickets = models.IntegerField(default=0)
    total_overs = models.FloatField(default=0.0) # e.g. 10.2
    
    # Extras aggregate
    extra_runs = models.IntegerField(default=0)
    
    is_completed = models.BooleanField(default=False)
    is_declared = models.BooleanField(default=False)

    class Meta:
        unique_together = ('match', 'team', 'innings')
        
    def __str__(self):
        return f"{self.team.short_name} - {self.total_runs}/{self.total_wickets} ({self.total_overs})"

class BattingScore(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='batting_scores')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    innings = models.IntegerField()
    
    runs = models.IntegerField(default=0)
    balls_faced = models.IntegerField(default=0)
    fours = models.IntegerField(default=0)
    sixes = models.IntegerField(default=0)
    
    strike_rate = models.FloatField(default=0.0)
    
    is_out = models.BooleanField(default=False)
    dismissal_text = models.CharField(max_length=100, blank=True, null=True)
    
    is_on_strike = models.BooleanField(default=False)

    class Meta:
        unique_together = ('match', 'player', 'innings')

class BowlingScore(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='bowling_scores')
    player = models.ForeignKey(Player, on_delete=models.CASCADE)
    innings = models.IntegerField()
    
    overs = models.FloatField(default=0.0)
    maidens = models.IntegerField(default=0)
    runs_conceded = models.IntegerField(default=0)
    wickets = models.IntegerField(default=0)
    economy = models.FloatField(default=0.0)

    class Meta:
        unique_together = ('match', 'player', 'innings')

class Ball(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='balls')
    innings = models.IntegerField()
    over_number = models.IntegerField() # 1-indexed (Over 1, Over 2...) or 0? Usually 0 indexed (0.1, 0.2) or 1 indexed in text. Let's use 1-indexed for human readability or 0 for logic. Reference: "ballOver". I'll use 0-indexed for logic (0.1 -> 0 over, ball 1).
    ball_number = models.IntegerField() # 1 to 6 (or more for extras)

    # Actors
    striker = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='balls_faced')
    non_striker = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='balls_at_non_striker')
    bowler = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='balls_bowled')
    
    # Runs
    runs_batter = models.IntegerField(default=0)
    extras = models.IntegerField(default=0)
    total_runs = models.IntegerField(default=0) # batter + extras
    
    # Extras Types
    is_wide = models.BooleanField(default=False)
    is_no_ball = models.BooleanField(default=False)
    is_bye = models.BooleanField(default=False)
    is_leg_bye = models.BooleanField(default=False)
    
    # Wicket
    is_wicket = models.BooleanField(default=False)
    dismissal_type = models.CharField(max_length=50, blank=True, null=True) # BOWLED, CAUGHT, etc
    dismissed_player = models.ForeignKey(Player, on_delete=models.SET_NULL, null=True, blank=True, related_name='dismissals')
    
    # Metadata
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.over_number}.{self.ball_number} - {self.total_runs} runs"
