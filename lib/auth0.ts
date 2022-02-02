import {initAuth0} from '@auth0/nextjs-auth0'
import {ISignInWithAuth0} from '@auth0/nextjs-auth0/dist/instance'
import {ISession} from '@auth0/nextjs-auth0/dist/session/session'
import {parse} from 'cookie'
import {IncomingMessage} from 'http'
import ms from 'ms'

import {IUser} from './user'

const cookieLifetime = ms('30 days') / 1000
const httpTimeout = ms('10s')
const scope = 'openid profile id_token'

/**
 * Auth0 is initialized with the origin taken from an incoming header. With Vercel Preview Deployments,
 * a single lambda may handle multiple origins. Ex: conveyal.dev, branch-git.conveyal.vercel.app,
 * and analysis-11234234.vercel.app. Therefore we initialize a specific auth0 instance for each origin
 * and store them based on that origin.
 */
const auth0s = {
  // [origin]: ISignInWithAuth0
}

function createAuth0(origin: string): ISignInWithAuth0 {
  if (process.env.NEXT_PUBLIC_AUTH_DISABLED === 'true') {
    return {
      handleCallback: async () => {},
      handleLogin: async () => {},
      handleLogout: async () => {},
      handleProfile: async () => {},
      getSession: async (): Promise<ISession> => ({
        createdAt: Date.now(),
        user: {
          name: 'local',
          'http://conveyal/accessGroup': 'local'
        },
        idToken: 'fake'
      }),
      requireAuthentication: (fn) => fn,
      tokenCache: () => ({
        getAccessToken: async () => ({})
      })
    }
  } else {
    return initAuth0({
      clientId: process.env.AUTH0_CLIENT_ID,
      clientSecret: process.env.AUTH0_CLIENT_SECRET,
      scope,
      domain: process.env.AUTH0_DOMAIN,
      redirectUri: `${origin}/api/callback`,
      postLogoutRedirectUri: origin,
      session: {
        cookieSecret: process.env.SESSION_COOKIE_SECRET,
        cookieLifetime,
        storeIdToken: true
      },
      oidcClient: {
        httpTimeout
      }
    })
  }
}

// Dyanmically create the Auth0 instance based upon a request
export default function initAuth0WithReq(
  req: IncomingMessage
): ISignInWithAuth0 {
  const host = req.headers.host
  const protocol = /^localhost(:\d+)?$/.test(host) ? 'http:' : 'https:'
  const origin = `${protocol}//${host}`
  if (auth0s[origin]) return auth0s[origin]
  auth0s[origin] = createAuth0(origin)
  return auth0s[origin]
}

/**
 * Flatten the session object and assign the accessGroup without the http portion.
 */
export async function getUser(req: IncomingMessage): Promise<IUser> {
  const auth0 = initAuth0WithReq(req)
  const session = await auth0.getSession(req)
  if (!session) {
    throw new Error('User session does not exist. User must be logged in.')
  }

  const user = {
    // This is a namespace for a custom claim. Not a URL: https://auth0.com/docs/tokens/guides/create-namespaced-custom-claims
    accessGroup: session.user['http://conveyal/accessGroup'],
    adminTempAccessGroup: null,
    email: session.user.name,
    idToken: session.idToken
  }

  if (user.accessGroup === process.env.NEXT_PUBLIC_ADMIN_ACCESS_GROUP) {
    const adminTempAccessGroup = parse(req.headers.cookie || '')
      .adminTempAccessGroup
    if (adminTempAccessGroup) user.adminTempAccessGroup = adminTempAccessGroup
  }

  return user
}

/**
 * Helper function for retrieving the access group.
 */
export async function getAccessGroup(req: IncomingMessage): Promise<string> {
  const user = await getUser(req)
  if (user.adminTempAccessGroup && user.adminTempAccessGroup.length > 0) {
    return user.adminTempAccessGroup
  }
  return user.accessGroup
}
