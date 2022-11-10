module Auth exposing (User, onPageLoad)

{-| The Auth module defines what the app should do when a user tries to access
a page that requires authentication

@docs User, onPageLoad

-}

import Auth.Action
import Dict
import Route exposing (Route)
import Route.Path
import Shared


{-| Signed-in user data. This data will be passed to pages that require
authentication to render. Pages that require authn can be identified by the
fact that they take this type as the first argument to their `page` function.
-}
type alias User =
    { name : String
    , token : String
    }


{-| Runs when the user vistis a page requiring authentication. The value
returned from this will determine what the app does. Broadly speaking it can:

  - Navigate to an authentication interface of some kind
  - Return a [User](#User), enabling the page to render
  - Display a loading view

-}
onPageLoad : Shared.Model -> Route () -> Auth.Action.Action User
onPageLoad _ _ =
    Auth.Action.replaceRoute
        { path = Route.Path.SignIn
        , query = Dict.empty
        , hash = Nothing
        }
