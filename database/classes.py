from . import *

class User:
    def __init__(self, user_id: int) -> None:
        self.user_id = user_id

    def exists(self):
        return not select(f"SELECT `user_id` FROM `mapguessr`.`users` WHERE user_id = '{self.user_id}'").value is None

    def create(self, guesses: int, correct: int, has_guessed: bool=False):
        update(f"INSERT INTO `mapguessr`.`users` (`user_id`, `guesses`, `correct`, `has_guessed`) VALUES ('{self.user_id}', '{guesses}', '{correct}', '{1 if has_guessed else 0}')")

    def get_guesses(self) -> int:
        return int(select(f"SELECT `guesses` FROM `mapguessr`.`users` WHERE user_id = '{self.user_id}'").value)
    
    def get_correct(self) -> int:
        return int(select(f"SELECT `correct` FROM `mapguessr`.`users` WHERE user_id = '{self.user_id}'").value)

    def increment_guesses(self, correct: bool):
        if self.exists():
            guesses = self.get_guesses() + 1
            add = f"`guesses` = '{guesses}'"
            if correct:
                correct_amt = self.get_correct() + 1
                add += f", `correct` = '{correct_amt}'"
            update(f"UPDATE `mapguessr`.`users` SET {add}, `has_guessed` = '1' WHERE `user_id` = '{self.user_id}'")
        else:
            self.create(1, 1 if correct else 0, 1)

    def has_guessed(self) -> bool:
        return select(f"SELECT `has_guessed` FROM `mapguessr`.`users` WHERE user_id = '{self.user_id}'").value == 1
    
    @staticmethod
    def reset_guessed():
        update(f"UPDATE `mapguessr`.`users` SET `has_guessed` = '0'")

    @staticmethod
    def get_top_correct(amount: int):
        return select(f"SELECT `user_id`, `guesses`, `correct` FROM `mapguessr`.`users` ORDER BY `correct` DESC LIMIT {amount}").value_all

class Guild:
    def __init__(self, guild_id: int) -> None:
        self.guild_id = guild_id

    def exists(self):
        return not select(f"SELECT `guild_id` FROM `mapguessr`.`guilds` WHERE guild_id = '{self.guild_id}'").value is None

    def set_channel(self, channel_id: int):
        if self.exists():
            update(f"UPDATE `mapguessr`.`guilds` SET `channel_id` = '{channel_id}' WHERE `guild_id` = '{self.guild_id}'")
        else:
            update(f"INSERT INTO `mapguessr`.`guilds` (`guild_id`, `channel_id`) VALUES ('{self.guild_id}', '{channel_id}')")

    def remove_channel(self):
        if self.exists():
            update(f"UPDATE `mapguessr`.`guilds` SET `channel_id` = '{None}' WHERE `guild_id` = '{self.guild_id}'")
    
    def get_channel(self):
        return select(f"SELECT `channel_id` FROM `mapguessr`.`guilds` WHERE guild_id = '{self.guild_id}'").value

    @staticmethod
    def get_all_channels():
        return select(f"SELECT `channel_id` FROM `mapguessr`.`guilds`").value_all

class Guess:
    def __init__(self, country: str) -> None:
        self.country = country

    def exists(self):
        return not select(f"SELECT `country` FROM `mapguessr`.`guesses` WHERE country = '{self.country}'").value is None

    def get_guesses(self):
        return select(f"SELECT `guesses` FROM `mapguessr`.`guesses` WHERE country = '{self.country}'").value

    def increment(self):
        if self.exists():
            guesses = self.get_guesses() + 1
            update(f"UPDATE `mapguessr`.`guesses` SET `guesses` = '{guesses}' WHERE `country` = '{self.country}'")
        else:
            update(f"INSERT INTO `mapguessr`.`guesses` (`country`, `guesses`) VALUES ('{self.country}', '{1}')")

    @staticmethod
    def clear_guesses():
        update("DELETE FROM `mapguessr`.`guesses`")

    @staticmethod
    def get_all_guesses():
        return select("SELECT * FROM `mapguessr`.`guesses` ORDER BY `guesses` DESC LIMIT 5").value_all

    @staticmethod
    def get_total_guesses():
        return select("SELECT SUM(`guesses`) FROM `mapguessr`.`guesses`").value
