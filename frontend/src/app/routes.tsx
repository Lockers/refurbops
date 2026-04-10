import { Navigate, createBrowserRouter } from 'react-router-dom';

import { RequireAuth } from '@/app/guards/RequireAuth';
import { RequireCapability } from '@/app/guards/RequireCapability';
import { RequireMfa } from '@/app/guards/RequireMfa';
import { RequireSetup } from '@/app/guards/RequireSetup';
import { AppShellLayout } from '@/app/shell/AppShell';
import { useSession } from '@/auth/hooks/useSession';
import { ChangePasswordPage } from '@/auth/pages/ChangePasswordPage';
import { AuthVerifiedPage } from '@/auth/pages/AuthVerifiedPage';
import { LoginPage } from '@/auth/pages/LoginPage';
import { MfaEnrollPage } from '@/auth/pages/MfaEnrollPage';
import { MfaPage } from '@/auth/pages/MfaPage';
import { SessionExpiredPage } from '@/auth/pages/SessionExpiredPage';
import { VerifyEmailPage } from '@/auth/pages/VerifyEmailPage';
import { BusinessDetailPage } from '@/foundation/businesses/pages/BusinessDetailPage';
import { BusinessListPage } from '@/foundation/businesses/pages/BusinessListPage';
import { CreateBusinessPage } from '@/foundation/businesses/pages/CreateBusinessPage';
import { AccessPendingPage } from '@/foundation/organisations/pages/AccessPendingPage';
import { OrganisationOverviewPage } from '@/foundation/organisations/pages/OrganisationOverviewPage';
import { OnboardingPage } from '@/foundation/setup/pages/OnboardingPage';
import { SetupHubPage } from '@/foundation/setup/pages/SetupHubPage';
import { SiteDetailPage } from '@/foundation/sites/pages/SiteDetailPage';
import { SubscriptionDetailPage } from '@/foundation/subscriptions/pages/SubscriptionDetailPage';
import { UserDetailPage } from '@/foundation/users/pages/UserDetailPage';
import { UserListPage } from '@/foundation/users/pages/UserListPage';
import { getDefaultLandingRoute } from '@/shared/lib/authz';

function AppIndexRedirect() {
  const { session, isLoading } = useSession();
  if (isLoading) return null;
  if (!session) return <Navigate to="/login" replace />;
  return <Navigate to={getDefaultLandingRoute(session)} replace />;
}

export const router = createBrowserRouter([
  { path: '/', element: <Navigate to="/login" replace /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/change-password', element: <ChangePasswordPage /> },
  { path: '/mfa/enroll', element: <MfaEnrollPage /> },
  { path: '/auth/verified', element: <AuthVerifiedPage /> },
  { path: '/verify-email', element: <VerifyEmailPage /> },
  { path: '/mfa', element: <MfaPage /> },
  { path: '/session-expired', element: <SessionExpiredPage /> },
  {
    path: '/app',
    element: (
      <RequireAuth>
        <RequireMfa>
          <AppShellLayout />
        </RequireMfa>
      </RequireAuth>
    ),
    children: [
      { index: true, element: <AppIndexRedirect /> },
      { path: 'overview', element: <OrganisationOverviewPage /> },
      { path: 'access-pending', element: <AccessPendingPage /> },
      {
        path: 'setup',
        element: (
          <RequireSetup>
            <SetupHubPage />
          </RequireSetup>
        ),
      },
      { path: 'onboarding', element: <OnboardingPage /> },
      {
        path: 'businesses',
        element: (
          <RequireCapability roles={['platform_owner', 'organisation_admin', 'business_owner']}>
            <BusinessListPage />
          </RequireCapability>
        ),
      },
      {
        path: 'businesses/new',
        element: (
          <RequireCapability roles={['platform_owner', 'organisation_admin', 'business_owner']}>
            <CreateBusinessPage />
          </RequireCapability>
        ),
      },
      {
        path: 'businesses/:businessId',
        element: (
          <RequireCapability roles={['platform_owner', 'organisation_admin', 'business_owner']}>
            <BusinessDetailPage />
          </RequireCapability>
        ),
      },
      {
        path: 'sites/:siteId',
        element: (
          <RequireCapability roles={['platform_owner', 'organisation_admin', 'business_owner']}>
            <SiteDetailPage />
          </RequireCapability>
        ),
      },
      {
        path: 'users',
        element: (
          <RequireCapability roles={['platform_owner', 'organisation_admin', 'business_owner']}>
            <UserListPage />
          </RequireCapability>
        ),
      },
      {
        path: 'users/:userId',
        element: (
          <RequireCapability roles={['platform_owner', 'organisation_admin', 'business_owner']}>
            <UserDetailPage />
          </RequireCapability>
        ),
      },
      {
        path: 'subscriptions/:businessId',
        element: (
          <RequireCapability roles={['platform_owner', 'organisation_admin', 'business_owner']}>
            <SubscriptionDetailPage />
          </RequireCapability>
        ),
      },
    ],
  },
  { path: '*', element: <Navigate to="/login" replace /> },
]);
