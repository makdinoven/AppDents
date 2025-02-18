import { FC } from 'react';
import { AppProps } from 'next/app';
import Head from 'next/head';
import { MantineProvider } from '@mantine/core';
import { ModalsProvider } from '@mantine/modals';
import { Notifications } from '@mantine/notifications';
import { QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';

import theme from 'theme';

import queryClient from 'query-client';

import PageConfig from './PageConfig';

import '@mantine/core/styles.layer.css';
import '@mantine/dates/styles.layer.css';
import '@mantine/notifications/styles.layer.css';
import '@mantine/dropzone/styles.layer.css';
import 'theme/globalStyles.css';

const App: FC<AppProps> = ({ Component, pageProps }) => (
  <>
    <Head>
      <title>DIS</title>
      <meta
        name="viewport"
        content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no, orientation=portrait"
      />
    </Head>

    <QueryClientProvider client={queryClient}>
      <MantineProvider theme={theme} withGlobalClasses>
        <ModalsProvider>
          <PageConfig>
            <Component {...pageProps} />
          </PageConfig>
        </ModalsProvider>

        <Notifications autoClose={10000} />
        <ReactQueryDevtools buttonPosition="bottom-left" />
      </MantineProvider>
    </QueryClientProvider>
  </>
);

export default App;
