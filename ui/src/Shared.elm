module Shared exposing
    ( Flags, decoder
    , Model, Msg
    , init, update, subscriptions
    )

{-| The Shared module handles global application state.

@docs Flags, decoder
@docs Model, Msg
@docs init, update, subscriptions

-}

import Api
import Data.User as User exposing (UserStatus)
import Effect exposing (Effect)
import Error
import Http
import Json.Decode
import Route exposing (Route)



-- FLAGS


{-| Data passed to the Elm application on startup from JS.
-}
type alias Flags =
    {}


{-| Instructions for turning JSON from JS into [Flags](#Flags). Shared.init
will recieve the result of running the decoder on the input provided to the app.
-}
decoder : Json.Decode.Decoder Flags
decoder =
    Json.Decode.succeed {}



-- INIT


{-| Global application state. Things that need to persist across all pages go
here. This is stuff like the current logged in user, auth tokens, translation
information, etc.
-}
type alias Model =
    { user : UserStatus }


{-| Runs when the app starts. It allows us to set up the initial
[Shared.Model](#Model) state by doing this like seting up default values,
looking up user preferences, loading stored credentials, etc.
-}
init : Result Json.Decode.Error Flags -> Route () -> ( Model, Effect Msg )
init _ _ =
    ( { user = User.loading }
    , Api.getConfig ConfigResponse
    )



-- UPDATE


{-| Things that can happen to update the shared state or trigger side effects.
In conjunction with [Shared.update](#update), this defines how our shared global
state evolves as things happen in the app.
-}
type Msg
    = ConfigResponse (Result Http.Error Api.Config)


{-| Runs whenever something emits a [Shared.Msg](#Msg). That can happen for a
number of reasons. Some examples are:

    - A Http request made fom this module completes
    - An update from [Shared.subscriptions](#subscriptions)
    - A page was configured to send it to update shared state

-}
update : Route () -> Msg -> Model -> ( Model, Effect Msg )
update _ msg model =
    case msg of
        ConfigResponse (Ok config) ->
            ( { model | user = User.updateConfig config model.user }, Effect.none )

        ConfigResponse (Err err) ->
            ( { model | user = User.fail (Error.configFailure err) }, Effect.none )



-- SUBSCRIPTIONS


{-| Allows us to trigger messages that update global state when something
outside of the application changes. For example, if you wanted to do something
on a particular time interval, you'd set it up here.
-}
subscriptions : Route () -> Model -> Sub Msg
subscriptions _ _ =
    Sub.none
