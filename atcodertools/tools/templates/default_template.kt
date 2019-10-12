import java.util.*

{% if mod %}
val MOD: Long = {{ mod }}
{% endif %}
{% if yes_str %}
val YES = "{{ yes_str }}"
{% endif %}
{% if no_str %}
val NO = "{{ no_str }}"
{% endif %}

fun main(args: Array<String>) {
    val sc = Scanner(System.`in`)

    {% if prediction_success %}
    {{ input_part }}
    solve({{ actual_arguments }})
    {% else %}
    // Failed to predict input format
    {% endif %}
}

{% if prediction_success %}
fun solve({{ formal_arguments }}) {
}
{% endif %}
