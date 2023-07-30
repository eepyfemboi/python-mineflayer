import assertpy

def inject(bot):
    def set_command_block(pos, command, options=None):
        if options is None:
            options = {}
        
        assertpy.asserts.assert_equal(bot.player.gamemode, 1, msg='The bot has to be in creative mode to open the command block window')
        assertpy.assert_not_equal(pos, None)
        assertpy.assert_not_equal(command, None)
        assertpy.assert_true(bot.block_at(pos).name.includes('command_block'), msg="The block isn't a command block")

        # Default values when a command block is placed in vanilla minecraft
        options['trackOutput'] = options.get('trackOutput', False)
        options['conditional'] = options.get('conditional', False)
        options['alwaysActive'] = options.get('alwaysActive', False)
        options['mode'] = options.get('mode', 2)  # Possible values: 0: SEQUENCE, 1: AUTO and 2: REDSTONE

        flags = 0
        flags |= int(options['trackOutput']) << 0  # 0x01
        flags |= int(options['conditional']) << 1  # 0x02
        flags |= int(options['alwaysActive']) << 2  # 0x04

        if bot.support_feature('usesAdvCmd') or bot.support_feature('usesAdvCdm'):
            plugin_channel_name = 'MC|AdvCdm' if bot.support_feature('usesAdvCdm') else 'MC|AdvCmd'

            proto = ProtoDef()

            proto.add_type('string', [
                'pstring',
                {
                    'countType': 'varint'
                }])

            proto.add_type(plugin_channel_name, [
                'container',
                [
                    {
                        'name': 'mode',
                        'type': 'i8'
                    },
                    {
                        'name': 'x',
                        'type': [
                            'switch',
                            {
                                'compareTo': 'mode',
                                'fields': {
                                    0: 'i32'
                                },
                                'default': 'void'
                            }
                        ]
                    },
                    {
                        'name': 'y',
                        'type': [
                            'switch',
                            {
                                'compareTo': 'mode',
                                'fields': {
                                    0: 'i32'
                                },
                                'default': 'void'
                            }
                        ]
                    },
                    {
                        'name': 'z',
                        'type': [
                            'switch',
                            {
                                'compareTo': 'mode',
                                'fields': {
                                    0: 'i32'
                                },
                                'default': 'void'
                            }
                        ]
                    },
                    {
                        'name': 'eid',
                        'type': [
                            'switch',
                            {
                                'compareTo': 'mode',
                                'fields': {
                                    1: 'i32'
                                },
                                'default': 'void'
                            }
                        ]
                    },
                    {
                        'name': 'command',
                        'type': 'string'
                    },
                    {
                        'name': 'trackOutput',
                        'type': 'bool'
                    }
                ]
            ])

            buffer = proto.create_packet_buffer(plugin_channel_name, {
                'mode': 0,
                'x': pos.x,
                'y': pos.y,
                'z': pos.z,
                'command': command,
                'trackOutput': options['trackOutput']
            })
            bot._client.write('custom_payload', {
                'channel': plugin_channel_name,
                'data': buffer
            })
        else:
            bot._client.write('update_command_block', {
                'location': pos,
                'command': command,
                'mode': options['mode'],
                'flags': flags
            })

    bot.set_command_block = set_command_block
