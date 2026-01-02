# Protocol Documentation
<a name="top"></a>

## Table of Contents

- [ondewo/survey/fhir.proto](#ondewo/survey/fhir.proto)
    - [CreateFHIRSurveyRequest](#ondewo.survey.CreateFHIRSurveyRequest)
    - [SurveyFHIRAnswersResponse](#ondewo.survey.SurveyFHIRAnswersResponse)
  
    - [FHIR](#ondewo.survey.FHIR)
  
- [ondewo/survey/survey.proto](#ondewo/survey/survey.proto)
    - [AgentSurveyRequest](#ondewo.survey.AgentSurveyRequest)
    - [AgentSurveyResponse](#ondewo.survey.AgentSurveyResponse)
    - [Answer](#ondewo.survey.Answer)
    - [Answer.UserInfo](#ondewo.survey.Answer.UserInfo)
    - [Choice](#ondewo.survey.Choice)
    - [CreateSurveyRequest](#ondewo.survey.CreateSurveyRequest)
    - [DeleteSurveyRequest](#ondewo.survey.DeleteSurveyRequest)
    - [GetAllSurveyAnswersRequest](#ondewo.survey.GetAllSurveyAnswersRequest)
    - [GetSurveyAnswersRequest](#ondewo.survey.GetSurveyAnswersRequest)
    - [GetSurveyRequest](#ondewo.survey.GetSurveyRequest)
    - [ListSurveysRequest](#ondewo.survey.ListSurveysRequest)
    - [ListSurveysResponse](#ondewo.survey.ListSurveysResponse)
    - [MultipleChoiceQuestion](#ondewo.survey.MultipleChoiceQuestion)
    - [MultipleParameterQuestion](#ondewo.survey.MultipleParameterQuestion)
    - [OpenQuestion](#ondewo.survey.OpenQuestion)
    - [Question](#ondewo.survey.Question)
    - [ScaleQuestion](#ondewo.survey.ScaleQuestion)
    - [ScaleQuestion.ScaleValue](#ondewo.survey.ScaleQuestion.ScaleValue)
    - [SingleChoiceQuestion](#ondewo.survey.SingleChoiceQuestion)
    - [SingleParameterQuestion](#ondewo.survey.SingleParameterQuestion)
    - [Survey](#ondewo.survey.Survey)
    - [SurveyAnswersResponse](#ondewo.survey.SurveyAnswersResponse)
    - [SurveyInfo](#ondewo.survey.SurveyInfo)
    - [UpdateSurveyRequest](#ondewo.survey.UpdateSurveyRequest)
  
    - [SubFlow](#ondewo.survey.SubFlow)
    - [Survey.AgentStatus](#ondewo.survey.Survey.AgentStatus)
  
    - [Surveys](#ondewo.survey.Surveys)
  
- [Scalar Value Types](#scalar-value-types)



<a name="ondewo/survey/fhir.proto"></a>
<p align="right"><a href="#top">Top</a></p>

## ondewo/survey/fhir.proto
Copyright 2020 ONDEWO GmbH

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

    <a href="http://www.apache.org/licenses/LICENSE-2.0">http://www.apache.org/licenses/LICENSE-2.0</a>

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License. (editesyntax = "proto3";


<a name="ondewo.survey.CreateFHIRSurveyRequest"></a>

### CreateFHIRSurveyRequest
Request message for creating a survey from FHIR format


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| fhir_questionnaire | [google.protobuf.Struct](#google.protobuf.Struct) |  | FHIR questionnaire on a gRPC Struct format |






<a name="ondewo.survey.SurveyFHIRAnswersResponse"></a>

### SurveyFHIRAnswersResponse
Response message containing survey answers in FHIR format


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| survey_id | [string](#string) |  | The project identifier for this survey. Equal to the parent of the corresponding Agent. Format: <pre><code>projects/&lt;Project ID&gt;/agent</code></pre> |
| fhir_questionnaire_responses | [google.protobuf.Struct](#google.protobuf.Struct) | repeated | all requested answers |





 <!-- end messages -->

 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="ondewo.survey.FHIR"></a>

### FHIR


| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| CreateFHIRSurvey | [CreateFHIRSurveyRequest](#ondewo.survey.CreateFHIRSurveyRequest) | [Survey](#ondewo.survey.Survey) | <p>Create a Survey from FHIR format and an empty NLU Agent for it</p> |
| GetFHIRSurveyAnswers | [GetSurveyAnswersRequest](#ondewo.survey.GetSurveyAnswersRequest) | [SurveyFHIRAnswersResponse](#ondewo.survey.SurveyFHIRAnswersResponse) | <p>Get Survey Answers on FHIR format</p> |
| GetAllFHIRSurveyAnswers | [GetAllSurveyAnswersRequest](#ondewo.survey.GetAllSurveyAnswersRequest) | [SurveyFHIRAnswersResponse](#ondewo.survey.SurveyFHIRAnswersResponse) | <p>Get all Survey Answers on FHIR format</p> |

 <!-- end services -->



<a name="ondewo/survey/survey.proto"></a>
<p align="right"><a href="#top">Top</a></p>

## ondewo/survey/survey.proto
Copyright 2020 ONDEWO GmbH

Licensed under the Apache License, Version 2.0 (the "License"); you may not use this file except in compliance with the License. You may obtain a copy of the License at

    <a href="http://www.apache.org/licenses/LICENSE-2.0">http://www.apache.org/licenses/LICENSE-2.0</a>

Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License. (editesyntax = "proto3";


<a name="ondewo.survey.AgentSurveyRequest"></a>

### AgentSurveyRequest
Request message for agent-related survey operations


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| survey_id | [string](#string) |  | The project identifier for this survey. Equal to the parent of the corresponding Agent. Format: <pre><code>projects/&lt;Project ID&gt;/agent</code></pre> |






<a name="ondewo.survey.AgentSurveyResponse"></a>

### AgentSurveyResponse
Response message for agent-related survey operations


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| parent | [string](#string) |  | The parent of an agent. Equal to the survey ID. Format: <pre><code>projects/&lt;Project ID&gt;/agent</code></pre> |






<a name="ondewo.survey.Answer"></a>

### Answer
An answer to a survey question collected during a session


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| question_nr | [int64](#int64) |  | the number of the question to which this answer belongs |
| session_id | [string](#string) |  | the ID of the session on which the answer was collected |
| answer_text | [string](#string) |  | Required; the full answer text |
| answer_parameter | [string](#string) |  | fixme: better names and doc-strings below Optional; contains the normalized value of the selected option (parameter) extracted |
| answer_parameter_original | [string](#string) |  | Optional; contains the original text of the selected option (parameter) extracted |
| anonymous | [bool](#bool) |  | True if the survey is anonymous, false otherwise |
| user_information | [Answer.UserInfo](#ondewo.survey.Answer.UserInfo) |  | User information if the survey is not anonymous |






<a name="ondewo.survey.Answer.UserInfo"></a>

### Answer.UserInfo
User information for non-anonymous surveys


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| first_name | [string](#string) |  | First name of the User to be surveyed |
| last_name | [string](#string) |  | Last name of the User to be surveyed |
| phone_number | [string](#string) |  | Phone number of the User to be surveyed |
| session_id | [string](#string) |  | the ID of the session on which the answer was collected |
| user_id | [string](#string) |  | Unique identifier of the User to be surveyed |






<a name="ondewo.survey.Choice"></a>

### Choice
<p>The Choice message defines one &quot;option&quot; for the SingleChoiceQuestion and MultipleChoiceQuestion question types</p>
<p>Example: <code>Choice(synonyms=[&quot;blue&quot;, &quot;blueish&quot;, &quot;pale blue&quot;, &quot;deep blue&quot;])</code></p>


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| synonyms | [string](#string) | repeated | The synonyms which are recognized as equivalent for identifying one option |
| follow_up_question | [Question](#ondewo.survey.Question) |  | Optional; Nested question if this specific choice gets chosen. Note: the follow-up question is only available for the SingleChoiceQuestion |
| value | [string](#string) |  | The &quot;canonical value&quot; (i.e. the entity value) |






<a name="ondewo.survey.CreateSurveyRequest"></a>

### CreateSurveyRequest
Request message for creating a new survey


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| survey | [Survey](#ondewo.survey.Survey) |  | The survey to create |






<a name="ondewo.survey.DeleteSurveyRequest"></a>

### DeleteSurveyRequest
Request message for deleting a survey


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| survey_id | [string](#string) |  | The project identifier for this survey. Equal to the parent of the corresponding Agent. Format: <pre><code>projects/&lt;Project ID&gt;/agent</code></pre> |






<a name="ondewo.survey.GetAllSurveyAnswersRequest"></a>

### GetAllSurveyAnswersRequest
Request message for retrieving all survey answers


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| survey_id | [string](#string) |  | The project identifier for this survey. Equal to the parent of the corresponding Agent. Format: <pre><code>projects/&lt;Project ID&gt;/agent</code></pre> |






<a name="ondewo.survey.GetSurveyAnswersRequest"></a>

### GetSurveyAnswersRequest
Request message for retrieving survey answers for a specific session or user


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| survey_id | [string](#string) |  | The project identifier for this survey. Equal to the parent of the corresponding Agent. Format: <pre><code>projects/&lt;Project ID&gt;/agent</code></pre> |
| session_id | [string](#string) |  | ID of one specific session on which survey answers were collected (contains survey_id) |
| user_id | [string](#string) |  | User Identifier. Note, if the survey is anonymous there will no identifier to filter on |
| user_phone_number | [string](#string) |  | User phone number. Note, if the survey is anonymous there will no identifier to filter on |






<a name="ondewo.survey.GetSurveyRequest"></a>

### GetSurveyRequest
Request message for retrieving a survey


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| survey_id | [string](#string) |  | The project identifier for this survey. Equal to the parent of the corresponding Agent. Format: <pre><code>projects/&lt;Project ID&gt;/agent</code></pre> |






<a name="ondewo.survey.ListSurveysRequest"></a>

### ListSurveysRequest
Request message for listing surveys with pagination support


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| page_token | [string](#string) |  | Optional. The next_page_token value returned from a previous list request. Example: <ul> <li>&quot;current_index-10--page_size-20&quot; - Start page -&gt; 10, Page size -&gt; 20</li> </ul> |






<a name="ondewo.survey.ListSurveysResponse"></a>

### ListSurveysResponse
<p>The response message for <a href="index.html#google.cloud.dialogflow.v2.Intents.ListIntents">Intents.ListIntents</a>.</p>


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| surveys | [Survey](#ondewo.survey.Survey) | repeated | The list of surveys. There will be a maximum number of items returned based on the page_token field in the request. |
| next_page_token | [string](#string) |  | Token to retrieve the next page of results, or empty if there are no more results in the list. |






<a name="ondewo.survey.MultipleChoiceQuestion"></a>

### MultipleChoiceQuestion
<p>A question for which exactly one or more out of a predefined set of options are expected as answers</p>
<p>Example: <code>MultipleChoiceQuestion(question_text=&apos;Which colors do you like?&apos;, choices=[Choice(synonyms=[&apos;red&apos;, &apos;reddisch&apos;]), Choice(synonyms=[&apos;blue&apos;, &apos;blueish&apos;]), Choice(synonyms=[&apos;yellow&apos;])])</code></p>


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| question_text | [string](#string) |  | The text which introduces the question (should be pronounceable) |
| choices | [Choice](#ondewo.survey.Choice) | repeated | List of choices which are accepted for this question Each Choice is represented by lists of synonyms. Note: needs to contain at least 2 choices |






<a name="ondewo.survey.MultipleParameterQuestion"></a>

### MultipleParameterQuestion
<p>MultipleParameterQuestion defines a question which prompts the user for one or several entities of one particular type</p>
<p>Example: <code>MultipleParameterQuestion(question_text=&apos;How old are your children?&apos;, parameter_type=&apos;sys.number&apos;)</code></p>


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| question_text | [string](#string) |  | The text which introduces the question (should be pronounceable) |
| parameter_type | [string](#string) |  | The display name of the entity (type) which is accepted as an answer to this question Note: the corresponding entity_type must exist (system entity type) and is not automatically created |






<a name="ondewo.survey.OpenQuestion"></a>

### OpenQuestion
<p>A question to which any kind of reply can be given and recorded</p>
<p>fixme: not working yet</p>


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| question_text | [string](#string) |  | The text which introduces the question (should be pronounceable) |






<a name="ondewo.survey.Question"></a>

### Question
A question that can be one of several question types: open-ended, single choice, multiple choice, scale, or parameter-based questions


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| open_question | [OpenQuestion](#ondewo.survey.OpenQuestion) |  | A question to which any kind of reply can be given and recorded |
| single_choice_question | [SingleChoiceQuestion](#ondewo.survey.SingleChoiceQuestion) |  | A question for which exactly one out of a predefined set of options is expected as answer |
| multiple_choice_question | [MultipleChoiceQuestion](#ondewo.survey.MultipleChoiceQuestion) |  | A question for which exactly one or more out of a predefined set of options are expected as answers |
| scale_question | [ScaleQuestion](#ondewo.survey.ScaleQuestion) |  | convenience wrapper around a SingleChoiceQuestion |
| single_parameter_question | [SingleParameterQuestion](#ondewo.survey.SingleParameterQuestion) |  | A question for which one or more entities of a particular type are expected as answers |
| multiple_parameter_question | [MultipleParameterQuestion](#ondewo.survey.MultipleParameterQuestion) |  | A question for which one or more entities of a particular type are expected as answers |






<a name="ondewo.survey.ScaleQuestion"></a>

### ScaleQuestion
A question for which an answer on a user-defined scale is expected


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| question_text | [string](#string) |  | The text which introduces the question (should be pronounceable) |
| min_value | [ScaleQuestion.ScaleValue](#ondewo.survey.ScaleQuestion.ScaleValue) |  | Minimum value and label for the scale |
| max_value | [ScaleQuestion.ScaleValue](#ondewo.survey.ScaleQuestion.ScaleValue) |  | Maximum value and label for the scale |






<a name="ondewo.survey.ScaleQuestion.ScaleValue"></a>

### ScaleQuestion.ScaleValue
Represents a value and label pair for scale question endpoints


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| value | [int32](#int32) |  | Numeric value for this scale point |
| label | [string](#string) |  | Human-readable label for this scale point |






<a name="ondewo.survey.SingleChoiceQuestion"></a>

### SingleChoiceQuestion
<p>A question for which exactly one out of a predefined set of options is expected as answer</p>
<p>Example: <code>SingleChoiceQuestion(question_text=&apos;Who is your favorite movie hero?&apos;, choices=[Choice(synonyms=[&apos;Bond&apos;, &apos;James Bond&apos;]), Choice(synonyms=[&apos;Batman&apos;]), Choice(synonyms=[&apos;Superman&apos;, &apos;Clark Kent&apos;])])</code></p>


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| question_text | [string](#string) |  | The text which introduces the question (should be pronounceable) |
| choices | [Choice](#ondewo.survey.Choice) | repeated | List of choices which are accepted for this question Each Choice is represented by lists of synonyms. Note: needs to contain at least 2 choices |






<a name="ondewo.survey.SingleParameterQuestion"></a>

### SingleParameterQuestion
<p>SingleParameterQuestion defines a question which prompts the user for one entity of a particular type</p>
<p>Example: <code>SingleParameterQuestion(question_text=&apos;How old are you?&apos;, parameter_type=&apos;sys.number&apos;)</code></p>


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| question_text | [string](#string) |  | The text which introduces the question (should be pronounceable) |
| parameter_type | [string](#string) |  | The display name of the entity (type) which is accepted as an answer to this question Note: the corresponding entity_type must exist (system entity type) and is not automatically created |






<a name="ondewo.survey.Survey"></a>

### Survey
A survey containing questions and metadata for conducting user surveys


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| survey_id | [string](#string) |  | The project identifier for this survey. Equal to the parent of the corresponding Agent. Format: <pre><code>projects/&lt;Project ID&gt;/agent</code></pre> Read-only in the Survey message (assigned by the back-end) |
| display_name | [string](#string) |  | Required. The (human readable) name of this survey |
| language_code | [string](#string) |  | Required. The language of the agent created for the survey. This is also the only supported language of the agent. ISO 639-1 language code |
| questions | [Question](#ondewo.survey.Question) | repeated | Required. List of questions to be asked during the survey. |
| survey_info | [SurveyInfo](#ondewo.survey.SurveyInfo) |  | Required. Information about the entity behind the survey, the purpose of the survey, legal stuff, etc. |
| exclude_subflows | [SubFlow](#ondewo.survey.SubFlow) | repeated | Optional. List of subflows excluded for this survey. |
| status | [Survey.AgentStatus](#ondewo.survey.Survey.AgentStatus) |  | Current status of the NLU Agent respecting to the Survey |






<a name="ondewo.survey.SurveyAnswersResponse"></a>

### SurveyAnswersResponse
Response message containing survey answers


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| survey_id | [string](#string) |  | The project identifier for this survey. Equal to the parent of the corresponding Agent. Format: <pre><code>projects/&lt;Project ID&gt;/agent</code></pre> |
| answers | [Answer](#ondewo.survey.Answer) | repeated | all requested answers |






<a name="ondewo.survey.SurveyInfo"></a>

### SurveyInfo
<p>Collect information about the entity behind the survey, the purpose of the survey, legal stuff, etc.</p>
<p>This is needed to generate meaningful messages and training data for some of the auto-generated intents.</p>


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| legal_entity | [string](#string) |  | Required unless SubFlow.LEGAL_ENTITY is deselected. The legal entity (company, research institute, etc.) on whose behalf the survey is performed |
| postal_address | [string](#string) |  | Required unless SubFlow.POSTAL_ADDRESS is deselected. The postal address to which callees can direct any requests. |
| email_address | [string](#string) |  | Required unless SubFlow.EMAIL_ADDRESS is deselected. The email address to which callees can direct any requests. |
| phone_number | [string](#string) |  | Required unless SubFlow.PHONE_NUMBER is deselected. The phone number to which callees can direct any requests. |
| phone_hours | [string](#string) |  | Required unless SubFlow.PHONE_HOURS is deselected. The phone hours during which callees can call (in pronounceable form). |
| expected_duration | [string](#string) |  | Required unless SubFlow.EXPECTED_DURATION is deselected. The expected duration of the survey (in pronounceable form) |
| purpose | [string](#string) |  | Required unless SubFlow.PURPOSE is deselected. An explanation regarding the purpose of the survey (in pronounceable form) |
| topic | [string](#string) |  | Required. A one-word explanation of the survey topic (in pronounceable form) |
| legal_disclaimer | [string](#string) |  | Required. A pronounceable explanation of the legal implications of participating in the survey. For example: &quot;Your answers during this survey will be stored anonymously for the next two years and then deleted.&quot; Should be formulated such that the agent can afterwards ask for the consent of the user. Example for how the agent could continue: &quot;Are you willing to participate in this survey?&quot; |
| anonymous | [bool](#bool) |  | Optional. Defaults to False. Allows the definition of a survey as anonymous or not. If the survey is not anonymous, the name of the people as well as their number will be recorded |






<a name="ondewo.survey.UpdateSurveyRequest"></a>

### UpdateSurveyRequest
Request message for updating an existing survey


| Field | Type | Label | Description |
| ----- | ---- | ----- | ----------- |
| survey | [Survey](#ondewo.survey.Survey) |  | Updated survey. Note: the ID must refer to an existing survey which will be updated |
| update_mask | [google.protobuf.FieldMask](#google.protobuf.FieldMask) |  | Optional. Field mask that defines which fields get updated. Default: all fields are updated. Example: <code>update_mask = FieldMask([&apos;survey.display_name&apos;, &apos;survey.questions&apos;])</code> |





 <!-- end messages -->


<a name="ondewo.survey.SubFlow"></a>

### SubFlow
<p>Enumeration of (some of) the subflows which are created by default</p>
<p>This can be used to &quot;switch off&quot; particular subflows when creating an agent during CreateSurvey</p>
<p>Subflows are defined as one of the following:</p>
<ul>
  <li>sequences of intents A -&gt; B_1, ..., B_n -&gt; ... -&gt; Z_1, ..., Z_m which are linked by context relationships such that the first intent in the sequence can always be triggered</li>
  <li>single intents which can always be triggered</li>
</ul>

| Name | Number | Description |
| ---- | ------ | ----------- |
| SUBFLOW_UNSPECIFIED | 0 | Not specified. This value should be never used. |
| BOT | 1 | The subflow allowing the user to inquire whether s/he is talking to a bot |
| LEGAL_ENTITY | 2 | The subflow allowing the user to inquire about the legal entity |
| POSTAL_ADDRESS | 3 | The subflow allowing the user to inquire about the postal address |
| EMAIL_ADDRESS | 4 | The subflow allowing the user to inquire about the email address |
| PHONE_NUMBER | 5 | The subflow allowing the user to inquire about the phone number |
| PHONE_HOURS | 6 | The subflow allowing the user to inquire about the phone hours |
| EXPECTED_DURATION | 7 | The subflow allowing the user to inquire about the expected duration of the survey |
| PURPOSE | 8 | The subflow allowing the user to inquire about the purpose of the survey |



<a name="ondewo.survey.Survey.AgentStatus"></a>

### Survey.AgentStatus


| Name | Number | Description |
| ---- | ------ | ----------- |
| TO_BE_INITIALIZED | 0 | Agent has not been initialized yet |
| UPDATED | 1 | Agent has been successfully updated and is current |
| UPDATING | 2 | Agent is currently being updated |
| OUTDATED | 3 | Agent is outdated and needs to be updated |


 <!-- end enums -->

 <!-- end HasExtensions -->


<a name="ondewo.survey.Surveys"></a>

### Surveys


| Method Name | Request Type | Response Type | Description |
| ----------- | ------------ | ------------- | ------------|
| CreateSurvey | [CreateSurveyRequest](#ondewo.survey.CreateSurveyRequest) | [Survey](#ondewo.survey.Survey) | <p>Create a Survey and an empty NLU Agent for it</p> |
| GetSurvey | [GetSurveyRequest](#ondewo.survey.GetSurveyRequest) | [Survey](#ondewo.survey.Survey) | <p>Retrieve a Survey message from the Database and return it</p> |
| UpdateSurvey | [UpdateSurveyRequest](#ondewo.survey.UpdateSurveyRequest) | [Survey](#ondewo.survey.Survey) | <p>Update an existing Survey message from the Database and return it</p> |
| DeleteSurvey | [DeleteSurveyRequest](#ondewo.survey.DeleteSurveyRequest) | [.google.protobuf.Empty](#google.protobuf.Empty) | <p>Delete a survey and its associated agent (if existent)</p> |
| ListSurveys | [ListSurveysRequest](#ondewo.survey.ListSurveysRequest) | [ListSurveysResponse](#ondewo.survey.ListSurveysResponse) | <p>Returns the list of all surveys in the server</p> |
| GetSurveyAnswers | [GetSurveyAnswersRequest](#ondewo.survey.GetSurveyAnswersRequest) | [SurveyAnswersResponse](#ondewo.survey.SurveyAnswersResponse) | <p>Retrieve answers to survey questions collected in interactions with a survey agent for a specific session</p> |
| GetAllSurveyAnswers | [GetAllSurveyAnswersRequest](#ondewo.survey.GetAllSurveyAnswersRequest) | [SurveyAnswersResponse](#ondewo.survey.SurveyAnswersResponse) | <p>Retrieve all answers to survey questions collected in interactions with a survey agent in any session</p> |
| CreateAgentSurvey | [AgentSurveyRequest](#ondewo.survey.AgentSurveyRequest) | [AgentSurveyResponse](#ondewo.survey.AgentSurveyResponse) | <p>Populate and configures an NLU Agent from a Survey</p> |
| UpdateAgentSurvey | [AgentSurveyRequest](#ondewo.survey.AgentSurveyRequest) | [AgentSurveyResponse](#ondewo.survey.AgentSurveyResponse) | <p>Update an NLU agent from a survey</p> |
| DeleteAgentSurvey | [AgentSurveyRequest](#ondewo.survey.AgentSurveyRequest) | [.google.protobuf.Empty](#google.protobuf.Empty) | <p>Deletes all data of an NLU agent associated to a survey</p> |

 <!-- end services -->



## Scalar Value Types

| .proto Type | Notes | C++ | Java | Python | Go | C# | PHP | Ruby |
| ----------- | ----- | --- | ---- | ------ | -- | -- | --- | ---- |
| <a name="double" /> double |  | double | double | float | float64 | double | float | Float |
| <a name="float" /> float |  | float | float | float | float32 | float | float | Float |
| <a name="int32" /> int32 | Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint32 instead. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="int64" /> int64 | Uses variable-length encoding. Inefficient for encoding negative numbers – if your field is likely to have negative values, use sint64 instead. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="uint32" /> uint32 | Uses variable-length encoding. | uint32 | int | int/long | uint32 | uint | integer | Bignum or Fixnum (as required) |
| <a name="uint64" /> uint64 | Uses variable-length encoding. | uint64 | long | int/long | uint64 | ulong | integer/string | Bignum or Fixnum (as required) |
| <a name="sint32" /> sint32 | Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int32s. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="sint64" /> sint64 | Uses variable-length encoding. Signed int value. These more efficiently encode negative numbers than regular int64s. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="fixed32" /> fixed32 | Always four bytes. More efficient than uint32 if values are often greater than 2^28. | uint32 | int | int | uint32 | uint | integer | Bignum or Fixnum (as required) |
| <a name="fixed64" /> fixed64 | Always eight bytes. More efficient than uint64 if values are often greater than 2^56. | uint64 | long | int/long | uint64 | ulong | integer/string | Bignum |
| <a name="sfixed32" /> sfixed32 | Always four bytes. | int32 | int | int | int32 | int | integer | Bignum or Fixnum (as required) |
| <a name="sfixed64" /> sfixed64 | Always eight bytes. | int64 | long | int/long | int64 | long | integer/string | Bignum |
| <a name="bool" /> bool |  | bool | boolean | boolean | bool | bool | boolean | TrueClass/FalseClass |
| <a name="string" /> string | A string must always contain UTF-8 encoded or 7-bit ASCII text. | string | String | str/unicode | string | string | string | String (UTF-8) |
| <a name="bytes" /> bytes | May contain any arbitrary sequence of bytes. | string | ByteString | str | []byte | ByteString | string | String (ASCII-8BIT) |
