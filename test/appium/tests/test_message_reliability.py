import pytest
import random
import string
from timeit import timeit

import time
from selenium.common.exceptions import TimeoutException

from tests import info
from tests.base_test_case import MultipleDeviceTestCase
from views.sign_in_view import SignInView


def wrapper(func, *args, **kwargs):
    def wrapped():
        return func(*args, **kwargs)

    return wrapped


def create_chart(user_1: dict, user_2: dict):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(nrows=1, ncols=1, figsize=(15, 7))
    time_1 = sorted(user_1['message_time'])
    ax.plot([i / 60 for i in time_1], [user_1['message_time'][i] for i in time_1],
            'o-', color='#0c0fea', label=user_1['name'])
    time_2 = sorted(user_2['message_time'])
    ax.plot([i / 60 for i in time_2], [user_2['message_time'][i] for i in time_2],
            'o-', color='#f61e06', label=user_2['name'])
    sent_messages = user_1['sent_messages'] + user_2['sent_messages']
    # title = "User A: sent messages: {}, received messages: {}, connection problem message appeared {} times" \
    #         "\nUser B: sent messages: {}, received messages: {}, connection problem message appeared {} times".format(
    #     user_1['sent_messages'], len(user_1['message_time']), user_1['connection_problem'], user_2['sent_messages'],
    #     len(user_2['message_time']), user_2['connection_problem'])
    title = "User A: sent messages: {}, received messages: {}" \
            "\nUser B: sent messages: {}, received messages: {}".format(user_1['sent_messages'],
                                                                        len(user_1['message_time']),
                                                                        user_2['sent_messages'],
                                                                        len(user_2['message_time']))
    if sent_messages:
        title += "\nReceived messages: {}%".format(
            round((len(user_1['message_time']) + len(user_2['message_time'])) / sent_messages * 100, ndigits=2))
    plt.title(title)
    plt.xlabel('chat session duration, minutes')
    plt.ylabel('time to receive a message, seconds')
    plt.legend()
    fig.savefig('chart.png')


@pytest.mark.message_reliability
class TestMessageReliability(MultipleDeviceTestCase):

    def test_message_reliability(self, messages_number, message_wait_time, connection_problem_wait_time):
        user_a_sent_messages = 0
        user_a_received_messages = 0
        user_a_connection_problem = 0
        user_b_sent_messages = 0
        user_b_received_messages = 0
        user_b_connection_problem = 0
        user_a_message_timing = dict()
        user_b_message_timing = dict()
        try:
            self.create_drivers(2, max_duration=10800, custom_implicitly_wait=2)
            device_1, device_2 = SignInView(self.drivers[0]), SignInView(self.drivers[1])
            device_1.create_user(username='user_a')
            device_2.create_user(username='user_b')
            device_1_home, device_2_home = device_1.get_home_view(), device_2.get_home_view()
            device_2_public_key = device_2_home.get_public_key()
            device_2_home.home_button.click()
            device_1_home.add_contact(device_2_public_key)
            device_1_chat = device_1_home.get_chat_view()
            device_2_home.element_by_text('user_a', 'button').click()
            device_2_chat = device_2_home.get_chat_view()
            device_2_chat.add_to_contacts.click()
            device_2_chat.chat_message_input.send_keys('hello')
            device_2_chat.send_message_button.click()
            device_1_chat.find_full_text('hello', wait_time=message_wait_time)

            connection_problem_timing = []
            start_time = time.time()
            for i in range(int(messages_number / 2)):

                # element = device_2_chat.element_by_text('Messages connection problem')
                # if element.is_element_present(1):
                #     user_b_connection_problem += 1
                #     connection_problem_timing.append(
                #         timeit(wrapper(element.wait_for_element_not_present, connection_problem_wait_time), number=1))

                # message_1 = ''.join(random.sample(string.ascii_lowercase + ' ' * 5, k=random.randint(3, 20))) + \
                #             random.sample(string.ascii_lowercase, k=1)[0]
                message_1 = ''.join(random.sample(string.ascii_lowercase, k=10))
                device_1_chat.chat_message_input.send_keys(message_1)
                device_1_chat.send_message_button.click()
                user_a_sent_messages += 1
                try:
                    user_b_receive_time = timeit(wrapper(device_2_chat.find_full_text, message_1, message_wait_time),
                                                 number=1)
                    duration_time = round(time.time() - start_time, ndigits=2)
                    user_b_message_timing[duration_time] = user_b_receive_time
                    user_b_received_messages += 1
                except TimeoutException:
                    info("Message with text '%s' was not received by user_b" % message_1)
                # element = device_1_chat.element_by_text('Messages connection problem')
                # if element.is_element_present(1):
                #     user_a_connection_problem += 1
                #     connection_problem_timing.append(
                #         timeit(wrapper(element.wait_for_element_not_present, connection_problem_wait_time), number=1))

                # message_2 = ''.join(random.sample(string.ascii_uppercase + ' ' * 5, k=random.randint(3, 20))) + \
                #             random.sample(string.ascii_lowercase, k=1)[0]
                message_2 = ''.join(random.sample(string.ascii_lowercase, k=10))
                device_2_chat.chat_message_input.send_keys(message_2)
                device_2_chat.send_message_button.click()
                user_b_sent_messages += 1
                try:
                    user_a_receive_time = timeit(wrapper(device_1_chat.find_full_text, message_2, message_wait_time),
                                                 number=1)
                    duration_time = round(time.time() - start_time, ndigits=2)
                    user_a_message_timing[duration_time] = user_a_receive_time
                    user_a_received_messages += 1
                except TimeoutException:
                    info("Message with text '%s' was not received by user_a" % message_2)
        finally:
            create_chart(
                user_1={'name': 'user_a', 'message_time': user_a_message_timing, 'sent_messages': user_a_sent_messages,
                        'connection_problem': user_a_connection_problem},
                user_2={'name': 'user_b', 'message_time': user_b_message_timing, 'sent_messages': user_b_sent_messages,
                        'connection_problem': user_b_connection_problem})
