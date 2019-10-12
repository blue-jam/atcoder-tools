from typing import Optional, Any, Dict, List

from atcodertools.codegen.code_style_config import CodeStyleConfig
from atcodertools.codegen.models.code_gen_args import CodeGenArgs
from atcodertools.codegen.template_engine import render
from atcodertools.fmtprediction.models.format import Format, Pattern, SingularPattern, ParallelPattern, \
    TwoDimensionalPattern
from atcodertools.fmtprediction.models.type import Type
from atcodertools.fmtprediction.models.variable import Variable


class KotlinCodeGenerator:
    def __init__(self,
                 format_: Optional[Format[Variable]],
                 config: CodeStyleConfig):
        self._format = format_
        self._config = config

    def generate_parameters(self) -> Dict[str, Any]:
        if self._format is None:
            return dict(prediction_success=False)

        return dict(
            formal_arguments=self._formal_arguments(),
            actual_arguments=self._actual_arguments(),
            input_part=self._input_part(),
            prediction_success=True
        )

    def _input_part(self) -> str:
        lines = sum(
            [self._render_pattern(pattern)
             for pattern in self._format.sequence],
            []
        )
        return '\n{}'.format(self._config.indent(1)).join(lines)

    def _convert_type(self, type_: Type) -> str:
        if type_ == Type.float:
            return 'Double'
        elif type_ == Type.int:
            return 'Long'
        elif type_ == Type.str:
            return 'String'
        else:
            raise NotImplementedError

    def _get_declaration_type(self, var: Variable) -> str:
        """
            :param var: information of a variable which the function generates a type declaration for
            :return: the type declaration for the variable, e.g. "Long" and "ArrayList<String>"
        """
        variable_type = self._convert_type(var.type)
        for _ in range(var.dim_num()):
            variable_type = 'Array<{}>'.format(variable_type)
        return variable_type

    def _actual_arguments(self) -> str:
        """
            :return the string form of actual arguments e.g. "N, K, a"
        """
        return ', '.join([v.name for v in self._format.all_vars()])

    def _formal_arguments(self) -> str:
        """
            :return the string form of formal arguments e.g. "N: Long, K: Long, a: ArrayList<Long>"
        """
        return ', '.join([
            '{name}: {decl_type}'.format(
                decl_type=self._get_declaration_type(v),
                name=v.name
            ) for v in self._format.all_vars()
        ])

    def _get_default_value_for_type(self, type_: Type) -> str:
        """
            :return: the default value for the type e.g. 0L for Long
        """
        if type_ == Type.float:
            return '0.0'
        elif type_ == Type.int:
            return '0L'
        elif type_ == Type.str:
            return '""'
        else:
            raise NotImplementedError

    def _generate_declaration(self, var: Variable) -> str:
        """
        :return: Create declaration part E.g. array[1..n] -> val array = Array(n-1+1) {0L};
        """
        if var.dim_num() > 2:
            raise NotImplementedError

        declaration_type = self._get_declaration_type(var)

        if var.dim_num() == 0:
            return 'var {name}: {type}'.format(name=var.name, type=declaration_type)

        dims = filter(
            lambda n: n is not None,
            [var.second_index, var.first_index]
        )
        declaration = self._get_default_value_for_type(var.type)
        for dim in dims:
            declaration = 'Array(({}).toInt())'.format(
                dim.get_length()
            ) + '{' + declaration + '}'

        return 'val {name} = {declaration}'.format(name=var.name, declaration=declaration)

    def _input_code_for_var(self, var: Variable) -> str:
        name = self._get_var_name(var)
        if var.type == Type.float:
            return '{} = sc.nextDouble()'.format(name)
        elif var.type == Type.int:
            return '{} = sc.nextLong()'.format(name)
        elif var.type == Type.str:
            return '{} = sc.next()'.format(name)
        else:
            raise NotImplementedError

    @staticmethod
    def _get_var_name(var: Variable) -> str:
        name = var.name
        for index_variable in ['i', 'j'][:var.dim_num()]:
            name += '[({}).toInt()]'.format(index_variable)

        return name

    def _render_pattern(self, pattern: Pattern) -> List[str]:
        lines = [self._generate_declaration(var) for var in pattern.all_vars()]

        representative_var: Variable = pattern.all_vars()[0]
        if isinstance(pattern, SingularPattern):
            lines.append(self._input_code_for_var(representative_var))
        elif isinstance(pattern, ParallelPattern):
            lines += self._wrap_with_loop(
                [self._input_code_for_var(var) for var in pattern.all_vars()],
                'i',
                representative_var.first_index.get_length()
            )
        elif isinstance(pattern, TwoDimensionalPattern):
            inner_loop = self._wrap_with_loop(
                [self._input_code_for_var(var) for var in pattern.all_vars()],
                'j',
                representative_var.second_index.get_length()
            )
            lines += self._wrap_with_loop(
                inner_loop,
                'i',
                representative_var.first_index.get_length()
            )

        return lines

    def _wrap_with_loop(self, lines: List[str], loop_variable: str, length: int) -> List[str]:
        wrapped_lines = [
            'for ({loop_variable} in 0 until {length}) {{'.format(
                loop_variable=loop_variable,
                length=length
            )]
        wrapped_lines += [self._config.indent(1) + line for line in lines]
        wrapped_lines.append('}')

        return wrapped_lines


def main(args: CodeGenArgs) -> str:
    code_parameters = KotlinCodeGenerator(
        args.format,
        args.config
    ).generate_parameters()

    return render(
        args.template,
        mod=args.constants.mod,
        yes_str=args.constants.yes_str,
        no_str=args.constants.no_str,
        **code_parameters
    )
