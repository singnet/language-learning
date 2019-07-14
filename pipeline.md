# ULL Pipeline Execution
Pipeline is executed by `ull-cli` script responsible for parsing configuration file. It executes
each pipeline component specified in JSON configuration file. There are several pipeline components
available for now:
- text-parser - component responsible for tokenizing and parsing text files (only Link Grammar parser is
implemented in the current version of the library);
- grammar-learner - component which takes parses as input and produces grammar dictionaries in 
Link Grammar format;
- grammar-tester - takes previously induced grammar and produces parsing metrics while parsing input
corpus and comparing the outcome with well defined parses of the same corpus.
- dash-board - dash board component responsible for depicting tabular pipeline results.
- path-creator - pseudo component used to create directory structure.

The above list will be extended with further versions of the library.


## `ull-cli` Script
`ull-cli` parses each componet configuration and runs it either sequentialy or simultaneously in a 
separate process. You should supply properly compiled JSON configuration file when running the script.

```
ull-cli -C <config.json> [-p <number-of-processes>]

    config.json             - Pipeline configuration file.
    number-of-processes     - Integer value, specifying the number of processes the pipeline can derive.
```

## JSON Configuration File
Before making your own configuration file make sure you have studied sample configuration files in 
https://github.com/singnet/language-learning/tests/test-data/config/pipeline . For 
`POC-Turtle-GL-GT-DB.json` make sure you have changed line 37 to match the path of `language-learning`
directory on your computer.  


Each pipeline configuration file must consist of the list of available component configuration 
dictionaries. Each component dictionary section should have the following parameters:
- `component`
- `common-parameters` (may be ommited)
- `specific-parameters`

`component` is the string name of one of the available pipeline components. This parameter is 
mandatory.

`specific-parameters` is a list of dictionaries, where each dictionary specifies unique configuration
of the specified component. Pipeline script executes specified component as many times as the number 
of dictionaries in the list.
 
`common-parameters` is a dictionary of zero or many parameters common for all configurations of 
the specified component. It may be ommitted if unnecessary.

Each component code is executed as many times as the length of `specific-parameters` list. Each 
successive component followes the execution path of the previous one. If the previous component
has multiple execution paths specified by the `specific-parameters` section, each path is folloed
by the successive component unless explicitly specified by `follow_exec_path=false` parameter.

`type` is a string parameter that can be either "dynamic" or "static". Static components should be
declared in the very beginning of JSON configuration file. They are created once and live until the 
end of pipeline execution. Dynamic components are created and destroyed on the fly. If `type` is not
specified "dynamic" is used by default.


### Currently Available Components

|Component|Type|Description|
|---------|----|-----------|
|text-parser|dynamic| Text Parser component |
|grammar-learner|dynamic| Grammar Learner component|
|grammar-tester|dynamic| Grammar Tester component|
|parse-evaluator|dynamic| Parse Evaluator component|
|dash-board|static| Dash-board component|
|path-creator|static| Path Creator component|

### Built-in Variables

|Variable| Description|
|--------|------------| 
|%ROOT| Pipeline root directory|
|%LEAF| Absolute target path based on %ROOT and 'specific-parameters'|
|%RLEAF| Target path relative to %ROOT based on 'specific-parameters'|
|%PREV[.var]| Reference to previous component scope variable. When `.var` is not specified `%PREV.LEAF` is used.|  
|%RPREV| Relative target path of the previous component scope.|
|%RUN_COUNT| Sequential component run count number starting from 1 and incrementing with every single configuration defined in 'specific-parameters' section.|

You can refer any previously defined parameter of the current scope simply by specifying '%' followed
by parameter name e.g. `%input_grammar`. To refer any variable of the previous scope one can specify 
'%PREV.' followed by parameter name e.g. `%PREV.input_grammar`.

### `pre_exec_req` and `post_exec_req`

In some cases you may need to do something before or after the component is executed. For example you 
may need to create some directory or put some value into a dashboard. In order for that you can specify 
pre component execution and/or post component execution events. 

Both `pre-exec-req` and `post-exec-req` are lists of dictionaries. Each dictionary defines a single
static component request. The only mandatory parameter of each dictonary is `obj` which specifies the 
name of the object instance and requested method separated by period e.g. 
`"post-exec-req": [{"obj": "stat.set", "row": "1", "col": "2", "val": "{F1}"}]`. 


You can skip any of the previously created configurations during pipeline execution by simply
adding `"skip_configuration": true` parameter into configuration you want to skip.

### Configuration Options Available For `grammar-tester`


|  Parameter  |  Type  |                    Meaning                 |  Values |
|-------------|--------|--------------------------------------------|---------|
|input_grammar| string | Path to `.dict` file to be tested          | Any valid path |
|input_corpus | string | Path to corpus file or directory           | Any valid path |
|template_path| string | Path to a valid Link Grammar dictionary to be used as a template when creating new dictionary with generated `.dict` file | Any valid path |
|grammar_root | string | Path to a directory new dictionary will be created in | Any valid path |
|output_path  | string | Path to store output parse and statistics files | Any valid path | 
|ref_path     | string | Path to a single reference file, or directory | Any valid path |
|parse_format | string | Type of parse output | ull, diagram, postscript, constituent_tree |
|linkage_limit| integer| Maximum number of linkages for Link Grammar to generate | 1-10000 | 
|rm_grammar_dir| boolean | Force grammar tester to remove existing grammar dictionary directory if it already exists. |true/false|
|use_link_parser|boolean | Force grammar tester to use `link-parser` executable in a separate process as a parser.| true/false|
|ull_input|boolean| Tells grammar tester that `.ull` file is used as an input corpus. When set to `true` lines starting with a digit are filtered out.| true/false|
|ignore_left_wall|boolean| If set to `true` `LEFT-WALL` and period links are ignored when parse statistics is estimated.|true/false|
|ignore_period|boolean| Force grammar tester to ignore period when parse statistics is estimated.| true/false|
|calc_parse_quality|boolean| If set to `true` parse quality is calculated.|true/false|
|keep_caps|boolean| Capitalized tokens are left untouched if set to `true`, lowered otherwise.| true/false|
|keep_rwall|boolean| Keep RIGHT-WALL if set to `true`|true/false|
|strip_suffix|boolean| Strip off token suffix if set to `true`.|true/false|
|dup_dict_path|boolean| Duplicate subdirectory structure of `input_grammar` directory if set to `true`.|true/false|
|separate_stat|boolean| Produce separate statistics file for each corpus file if set to `true`.|true/false|
|store_dict_localy|boolean| Create dictionary subdirectory in the same subdirectory where output files are stored.|true/false|
|no_left_wall_in_ull|boolean| Do not write `LEFT-WALL` links to `.ull` output file.|true/false|
|existing_dict_dir|boolean| Treat a string specified by `input_grammar` as path to existing Link Grammar dictionary directory.|true/false|
|exclude_timeouted|boolean| Exclude from statistics computation records with exceeded timeout.|true/false|
|exclude_explosion|boolean| Exclude from statistics computation sentences causing combinatorial explosion during parsing.|true/false|
|strict_tokenization|boolean| Force an exception if tokenization of test and reference sentences mismatch. Only warning is generated if not set or set to `False`.|true/false|
|ignore_sentence_mismatch|boolean| Do not generate an exception if test and reference sentences mismatch.|true/false|


## Configuring File Dashboard

File dashboard is defined by TextFileDashboard class and responsible for representation 
of parsing result statistics in a single table. 

In the current version of the library dashboard is only available when using 
the script with `-C` option.

File dashboard configuration is defined in `.json` configuration file and 
only available when using `grammar-tester` script with `-C` option.   

Here is the list of configurable parameters:

`row_count` - Numeric value representing the number of rows, including 
headers, in the dashboard.  

`col_count` - Numeric value representing the number of columns in the 
dashboard.    

`row_key` - Format string used as a dictionary key when searching for 
row index number. Key format strings are explained later in this document.  

`col_key` - Format string, used as a dictionary key when searching for 
column index number. Key format strings are explained later in this document.

`value_keys` - List of format string parameters where each element defines
format string for corresponding data cell in the dashboard table.

`col_headers` - List of header string parameters. Because table header may
consist of multiple rows, each element of the list defines corresponding
header row. Each row is definded by one or many named parameters. 
In a simpliest case only `title` parameter may be specified. Header definition
is explained later in this document.

`row_indexes` - dictionary with row key values and lists of corresponding
row index numbers.  

`col_indexes` - dictionary with column key values and lists of corresponding
column indexes.

### How it works
Each dashboard class implements `on_statistics()` event handler which is 
invoked by the GrammarTester class instance every time the grammar file 
test against the given corpus is complete. There are several parameters 
supplied when calling the handler: list of graph nodes (dictionary path
subdirectories) given in reverse order i.e. `/home/alex/data/AGI-2018` is 
passed as `["AGI-2018", "data", "alex", "home"]`, parseability and parse 
quality data structures. The event handler makes up row and column key 
strings using `row_key` and `col_key` configuration parameters, finds
corresponding row and column indexes, makes up value string using `value_key`
format string and fills corresponding cell(s) of the table with the value
string.

### General Steps For File Dashboard Configuration
1. Define dashboard table structure.
2. Analyse graph (directory) structure and find out dashboard dimentions
and graph nodes responsible for row/column positioning inside the dashboard.
3. Define row/column key value format strings.
4. Define row/column key string/numeric row/column index relations.
5. Define headers structure.


### Key Format Parameters
`row_key`, `col_key` are Python format strings needed to make up strings 
used as dictionary keys to find corresponding row and column numbers.

`value_keys` is a list of format strings for each cell value in a table
row.

As in any Python format string `{0}` represents variable index. 

For `row_key` and `col_key` numeric value in curly braces represents graph 
(path) node index starting from zero. Because the number of nodes may 
vary, the nodes are passed in reverse order.
  
For `value_keys` format strings use named variables within curly braces.
Here is the list of available variables `nodes` (used with index), 
`parseability`, `parsequality`, `PQA`.

### Row And Column Search Definitions
There are two dictionaries created when `TextFileDashboard` class instance is initialized.
One of them defines a relation between graph (path) nodes and row index(s),
another one defines a relation between graph (path) nodes and column
index(s). Row and column indexes are represented by lists of numeric values
because one graph node value may influence multiple rows/columns in the
dashboard. Both dictionaries are initialized with corresponding `row_indexes`
and `col_indexes` configuration parameters. Key string in each of the above
mentioned parameters must correspond `row_key`/`col_key` format template.

### Column Headers
As soon as table header may have complex structure, parameter `col_headers` is 
represented by list of headers where each header is a list of columns. Each 
column is a dictionary. While each column header definition may consist of 
multiple named entries, only `title` is mandatory and should be assigned a 
text string. HTMLFileDashboard class instances may handle `col_span` and 
`row_span` attributes. 

### Multiple Pipeline File Access
In the latest version multiple processes file access made available. Now you can configure two `.json` configuration 
files to populate the same dash board file table. You have to create each `.json`
with exactly the same dashboard definition including file name and dimentions. You have to add `"multi_access": true` 
to allow multiple processe to write the same text file. If you do that the process checks if the file is already exists 
and if it does it locks it for exclusive use, read it, update read table with its own latest results, saves it and 
unlocks the file. 