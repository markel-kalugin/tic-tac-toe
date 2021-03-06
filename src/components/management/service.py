from terminalplot import plot

from src.database.model.user import User
from src.database.model.game import Game, GameResult, LeagueSeason
from src.handler import Handler
from src.components.main_menu.service import MainMenuService


class ManagementService:
    def __init__(self, db_session):
        self.db_session = db_session
        self.main_menu_service = MainMenuService(self.db_session)

    def show_player_list(self, handler, destination_component, destination_method):
        """
        This mixin is used to show a list of users before deleting and
         requesting detailed information about a user.

        :param handler: The handler from which this handler was called
        :param destination_component: Name of the component to get the route
        :param destination_method: Name of the component's method to get
         the route
        :return: List of handlers for displaying users and the "previous" item
        """

        user_list = self.db_session.query(User).all()
        result = []
        last_menu_item = 0
        for i, user in enumerate(user_list):
            last_menu_item = i
            _handler = Handler(
                id=i,
                name=user.nickname,
                component=destination_component,
                method=destination_method,
                kwargs={'user': user}
            )
            _handler.parent = handler
            result.append(_handler)
        previous = Handler(
            id=last_menu_item + 1,
            name='Previous',
            component='Utility',
            method='previous_menu_item'
        )
        previous.parent = handler
        result.append(previous)

        return result

    def show_player_details(self, user) -> None:
        """
        Here is an aggregated detailed description of the user,
         his personal rating table and the dynamics of the growth
         of his points for the chart

        :param user: User object from declarative data model
        :return: None
        """
        user_detail = self.__concat_user_detail(user)
        growing_chart = self.__calculate_point_growing_chart(user)

        print(f"""
        {'-' * 50}
        User detail:
        {'-' * 50}
        """)
        print(user_detail)
        print(f"""
        {'-' * 50}
        Ranking table:
        {'-' * 50}
        """)
        self.main_menu_service.show_ranking_table(user)
        if growing_chart:
            print(f"""
        {'-' * 50}
        Points growth dynamics:
        {'-' * 50}
            """)
            plot(*growing_chart)

    def __calculate_point_growing_chart(self, user):
        """
        Here the dynamics of the growth of points is calculated

        :param user: User object from declarative data model
        :return: lists of values in x, y coordinates
        """
        current_league = self.main_menu_service.get_last_league_season()
        game_results = self.db_session.query(
            GameResult
        ).join(
            Game, Game.id == GameResult.game_id
        ).join(
            LeagueSeason, LeagueSeason.id == Game.league_season_id
        ).filter(
            LeagueSeason.id == current_league.id
        ).filter(
            GameResult.user_id == user.id
        ).order_by(
            GameResult.game_id.asc()
        ).all()
        result = None
        if game_results:
            x = range(len(game_results))
            y = []
            points = 0
            for i in game_results:
                points += 2 if i.is_winner else 1
                y.append(points)
            result = x, y
        return result

    def __concat_user_detail(self, user):
        """
        Here labels and value are concatenated depending on the filling of the fields

        :param user: User object from declarative data model
        :return: Concatenated string with user detailed description
        """
        label = '''
                Only completed fields will be displayed in the user's detailed information
                '''
        if user.first_name or user.last_name:
            user.first_name = '' if user.first_name is None else user.first_name
            user.last_name = '' if user.last_name is None else user.last_name
            label += f'''
                Detail of player {user.first_name} {user.last_name}:
                '''
        if user.nickname:
            label += f'''
                Nickname: {user.nickname}'''
        if user.age:
            label += f'''
                Age: {user.age} years old'''
        if user.email:
            label += f'''
                Email: {user.email}'''
        label += '\n'
        return label

    def player_create(self) -> None:
        """
        A user is created here. If you do not fill in the
         required field, it will be filled in automatically.
         Also, if the filled fields do not pass validation,
         this algorithm will ask the user to enter the value
         again and again until the field is valid.
        Optional fields can be left blank

        :return: None
        """
        user = User()
        field_name = ''

        is_valid_form = False
        while not is_valid_form:
            try:
                print('''
        Field marked with * is required''')
                for field in (i for i in user.__table__.c if i.name != 'id'):
                    if user.__getattribute__(field.name) is None:
                        label = '* ' if not field.nullable else ''
                        label += field.name.capitalize().replace('_', ' ')
                        label += ': '
                        setattr(user, field_name, '')
                        setattr(user, field.name, input(label))
            except AssertionError as e:
                print(e.args[0])
                field_name = e.args[1]
            else:
                self.db_session.add(user)
                self.db_session.commit()
                is_valid_form = True

        print(f'''
        Player {user.first_name} {user.last_name} has been created with attributes:

        Nickname: {user.nickname}
        Age: {user.age} years old
        Email: {user.email}
        ''')

    def create_new_league_season(self) -> None:
        """
        Seasons are needed only to filter statistics for them

        :return: None
        """
        new_league_season_name = input('Enter new league season name: ')
        league_season = LeagueSeason(
            name=new_league_season_name
        )
        self.db_session.add(league_season)
        self.db_session.commit()
        print(f'''
        New league season {new_league_season_name} was created.''')
