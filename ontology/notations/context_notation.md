# Context-oriented Notation

## Purpose

The context-oriented notation is designed to analyze the sources and influences that shaped a particular statement. It helps identify:
- Which quotes influenced the statement
- Which cognitive biases affected the reasoning
- The relationship between the statement author and quote authors

## Key Features

1. **Quote Objects**
   - Each quote is represented as a separate object
   - Quotes can have an `author` property
   - The `author` property can be:
     * `self` - if the statement author is quoting themselves
     * Author's name - if quoting another person

2. **Bias Connections**
   - Biases are connected to statements they influenced
   - Multiple biases can be connected to a single statement
   - Bias connections show the cognitive patterns in reasoning
   - Statements without bias connections are placed in a dedicated "No Cognitive Biases" column

3. **Visualization**
   - Statements are shown as nodes
   - Quotes are connected to statements they influenced
   - Biases are connected to statements they affected
   - Author relationships are shown through quote properties
   - A dedicated "No Cognitive Biases" column is shown on the left for statements without bias connections

## Use Cases

- Analyzing the sources of arguments
- Identifying cognitive biases in reasoning
- Understanding the influence of external sources
- Tracking self-referential statements

## Example

```json
{
  "statements": [
    {
      "id": "s1",
      "text": "The project will be completed on time",
      "quotes": ["q1"],
      "biases": ["optimism_bias"]
    }
  ],
  "quotes": [
    {
      "id": "q1",
      "text": "We have enough resources",
      "author": "self"
    }
  ]
}
```

## Visualization

The context-oriented notation is particularly useful for:
- Showing the "family tree" of statements
- Highlighting the influence of external sources
- Identifying patterns of self-referential reasoning
- Mapping the spread of cognitive biases

## Описание
Контекстная нотация фокусируется на представлении утверждений в контексте их источников и искажений, где:
- Когнитивные искажения (biases) образуют цветные колонки
- Утверждения (statements) размещаются в соответствующих колонках 
- Цитаты (quotations) и контекст выделены в отдельный блок справа

## Визуальные элементы

### Узлы
- **Когнитивные искажения**: 
  - Отображаются в виде цветных колонок
  - Каждому искажению присваивается уникальный пастельный цвет из набора из 12 цветов
  - При количестве искажений более 12 цвета повторяются по кругу
- **Нет когнитивных искажений**:
  - Отображается как серая колонка слева
  - Содержит утверждения без связей с когнитивными искажениями
- **Утверждения**:
  - Отображаются в соответствующих колонках в зависимости от наличия связей с когнитивными искажениями
  - Размещаются в белых прямоугольниках внутри колонок
  - Если утверждение связано с несколькими искажениями:
    - Текст отображается в правом прямоугольнике
    - Пустые прямоугольники создаются в других колонках
    - Прямоугольники соединяются пунктирными линиями
- **Цитаты**: 
  - Отображаются в правом блоке "CONTEXT"
  - Равномерно распределены по вертикали

### Связи
- Пунктирные линии между прямоугольниками одного утверждения
- Нахождения объекта утверждения в колонки когнитивного искажения свидетельствует о связи
- Линии от утверждений к цитатам
- Цитаты связываются с правым прямоугольником утверждения

## Особенности
- Визуальное разделение на основную часть и контекст
- Цветовая дифференциация искажений
- Четкое представление связей между утверждениями и искажениями
- Компактное представление контекста
- Диаграмму в данной нотации можно сортировать по хронологии цитат либо хронологии утверждений - в зависимости от задач исследователя.

## Использование
```sh
python tools/render_graph.py <input_file> context
```

## Пример
![Пример контекстной нотации](cognitive_ontology_graph_context.png) 