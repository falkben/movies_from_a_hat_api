module Data.User exposing (User, UserStatus(..), fail, loading, updateConfig)

import Api
import Error exposing (Error)


type UserStatus
    = Loading
    | Loaded User
    | Failed Error


type alias User =
    { apiConfig : Api.Config }


loading : UserStatus
loading =
    Loading


updateConfig : Api.Config -> UserStatus -> UserStatus
updateConfig config userStatus =
    case userStatus of
        Loading ->
            Loaded { apiConfig = config }

        Loaded user ->
            Loaded { user | apiConfig = config }

        Failed err ->
            Failed err


fail : Error -> UserStatus
fail error =
    Failed error
