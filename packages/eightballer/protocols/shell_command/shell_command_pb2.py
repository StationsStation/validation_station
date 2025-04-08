"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_sym_db = _symbol_database.Default()
DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x13shell_command.proto\x12$aea.eightballer.shell_command.v0_1_0"\xf3\x08\n\x13ShellCommandMessage\x12o\n\x0ecommand_result\x18\x05 \x01(\x0b2U.aea.eightballer.shell_command.v0_1_0.ShellCommandMessage.Command_Result_PerformativeH\x00\x12q\n\x0fexecute_command\x18\x06 \x01(\x0b2V.aea.eightballer.shell_command.v0_1_0.ShellCommandMessage.Execute_Command_PerformativeH\x00\x12q\n\x0fexecution_error\x18\x07 \x01(\x0b2V.aea.eightballer.shell_command.v0_1_0.ShellCommandMessage.Execution_Error_PerformativeH\x00\x1a\xca\x01\n\tErrorCode\x12e\n\nerror_code\x18\x01 \x01(\x0e2Q.aea.eightballer.shell_command.v0_1_0.ShellCommandMessage.ErrorCode.ErrorCodeEnum"V\n\rErrorCodeEnum\x12\x1d\n\x19COMMAND_EXECUTION_FAILURE\x10\x00\x12\x11\n\rTIMEOUT_ERROR\x10\x01\x12\x13\n\x0fINVALID_COMMAND\x10\x02\x1a\xb7\x02\n\x1cExecute_Command_Performative\x12\x0f\n\x07command\x18\x01 \x01(\t\x12\x0c\n\x04args\x18\x02 \x03(\t\x12t\n\x07options\x18\x03 \x03(\x0b2c.aea.eightballer.shell_command.v0_1_0.ShellCommandMessage.Execute_Command_Performative.OptionsEntry\x12\x0f\n\x07timeout\x18\x04 \x01(\x05\x12\x16\n\x0etimeout_is_set\x18\x05 \x01(\x08\x12\x10\n\x08env_vars\x18\x06 \x01(\x0c\x12\x17\n\x0fenv_vars_is_set\x18\x07 \x01(\x08\x1a.\n\x0cOptionsEntry\x12\x0b\n\x03key\x18\x01 \x01(\t\x12\r\n\x05value\x18\x02 \x01(\t:\x028\x01\x1aP\n\x1bCommand_Result_Performative\x12\x0e\n\x06stdout\x18\x01 \x01(\t\x12\x0e\n\x06stderr\x18\x02 \x01(\t\x12\x11\n\texit_code\x18\x03 \x01(\x05\x1a\x9b\x01\n\x1cExecution_Error_Performative\x12R\n\x05error\x18\x01 \x01(\x0b2C.aea.eightballer.shell_command.v0_1_0.ShellCommandMessage.ErrorCode\x12\x0f\n\x07message\x18\x02 \x01(\t\x12\x16\n\x0emessage_is_set\x18\x03 \x01(\x08B\x0e\n\x0cperformativeb\x06proto3')
_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'shell_command_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
    DESCRIPTOR._loaded_options = None
    _globals['_SHELLCOMMANDMESSAGE_EXECUTE_COMMAND_PERFORMATIVE_OPTIONSENTRY']._loaded_options = None
    _globals['_SHELLCOMMANDMESSAGE_EXECUTE_COMMAND_PERFORMATIVE_OPTIONSENTRY']._serialized_options = b'8\x01'
    _globals['_SHELLCOMMANDMESSAGE']._serialized_start = 62
    _globals['_SHELLCOMMANDMESSAGE']._serialized_end = 1201
    _globals['_SHELLCOMMANDMESSAGE_ERRORCODE']._serialized_start = 429
    _globals['_SHELLCOMMANDMESSAGE_ERRORCODE']._serialized_end = 631
    _globals['_SHELLCOMMANDMESSAGE_ERRORCODE_ERRORCODEENUM']._serialized_start = 545
    _globals['_SHELLCOMMANDMESSAGE_ERRORCODE_ERRORCODEENUM']._serialized_end = 631
    _globals['_SHELLCOMMANDMESSAGE_EXECUTE_COMMAND_PERFORMATIVE']._serialized_start = 634
    _globals['_SHELLCOMMANDMESSAGE_EXECUTE_COMMAND_PERFORMATIVE']._serialized_end = 945
    _globals['_SHELLCOMMANDMESSAGE_EXECUTE_COMMAND_PERFORMATIVE_OPTIONSENTRY']._serialized_start = 899
    _globals['_SHELLCOMMANDMESSAGE_EXECUTE_COMMAND_PERFORMATIVE_OPTIONSENTRY']._serialized_end = 945
    _globals['_SHELLCOMMANDMESSAGE_COMMAND_RESULT_PERFORMATIVE']._serialized_start = 947
    _globals['_SHELLCOMMANDMESSAGE_COMMAND_RESULT_PERFORMATIVE']._serialized_end = 1027
    _globals['_SHELLCOMMANDMESSAGE_EXECUTION_ERROR_PERFORMATIVE']._serialized_start = 1030
    _globals['_SHELLCOMMANDMESSAGE_EXECUTION_ERROR_PERFORMATIVE']._serialized_end = 1185